import sys
import json
import time
import requests
import trader.constants
import trader.binance.helper
import trader.binance.trade
import trader.binance.account
import trader.ssb.helper
import trader.indicators

# Keep track of the individual config files
master_config_files = []


def update_and_save_config_file(config_instance):
    instance_symbol = config_instance['base_currency'] + config_instance['target_currency']

    for current_config_index in range(len(master_config_files)):

        current_config = master_config_files[current_config_index]
        current_symbol = current_config['base_currency'] + current_config['target_currency']

        if instance_symbol == current_symbol:
            master_config_files[current_config_index] = config_instance
            trader.ssb.helper.write_config_file(master_config_files)
            return

    raise Exception(f'The symbol {instance_symbol} was not found in the {master_config_files}')

def perform_bot_operations(config, api_key, secret_key, print_out):

    base_currency = config['base_currency']
    target_currency = config['target_currency']
    buy_on_next_trade = config['buy_on_next_trade']
    trade_amount_buy = config['trade_amount_buy']
    trade_wealth_percent_sell = config['trade_wealth_percent_sell']
    last_operation_price = config['last_operation_price']
    prevent_loss = config['prevent_loss']

    symbol = base_currency + target_currency
    try:
        current_price = trader.binance.trade.get_current_trade_ratio(symbol)
    except requests.ConnectionError as ex:
        trader.ssb.helper.error_log(f'Failed while fetching the current price for {symbol}, {ex}', print_out)
        return

    total_indicator_count = 5
    # Check the indicator signals
    buy_signal = 0
    sell_signal = 0

    # RSI indicator
    rsi_margin = 4.0
    rsi = trader.indicators.get_rsi(symbol, '4h', moving_average=0, data_count=14)
    if rsi >= 70 - rsi_margin:
        sell_signal += 1
    elif rsi <= 30 + rsi_margin:
        buy_signal += 1

    # Bollinger bands indicator
    (upper, _, lower) = trader.indicators.get_bollinger_bands(symbol, '4h', 20)
    if current_price > upper:
        sell_signal += 1
    elif current_price < lower:
        buy_signal += 1

    # Simple moving average
    sma = trader.indicators.get_sma(symbol, '4h', 9)
    if current_price > sma:
        sell_signal += 1
    elif current_price < sma:
        buy_signal += 1

    # Exponential moving average (4h)
    ema = trader.indicators.get_ema(symbol, '4h', 9)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1

    # Exponential moving average (1d)
    ema = trader.indicators.get_ema(symbol, '1d', 9)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1

    if buy_on_next_trade:
        if total_indicator_count == buy_signal:
            target_amount = trade_amount_buy
            quantity = target_amount / current_price
            result = trader.binance.trade.create_market_order(api_key, secret_key, symbol, 'BUY', quantity)
            print(result)
            if result['status'] != 'FILLED':
                print('Response status was not FILLED, won\'t update config...')
                return
            config['buy_on_next_trade'] = False
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)
            trader.ssb.helper.log(f'Bought {quantity} {base_currency} for {target_amount} '
                f'{target_currency} ( {symbol} -> {current_price} )', print_out)
    else:
        if total_indicator_count == sell_signal:
            if prevent_loss and last_operation_price > current_price:
                print(f'Won\'t sell {base_currency} to prevent loss')
            else:
                # Create sell order
                base_amount = trader.binance.account.get_free_balance_amount(api_key, secret_key, base_currency)
                # Calculate total amount that we can trade
                base_amount = base_amount * trade_wealth_percent_sell / 100
                result = trader.binance.trade.create_market_order(api_key, secret_key, symbol, 'SELL', base_amount)
                print(result)
                if result['status'] != 'FILLED':
                    print('Response status was not FILLED, won\'t update config...')
                    return
                config['buy_on_next_trade'] = True
                config['last_operation_price'] = current_price
                update_and_save_config_file(config)
                trader.ssb.helper.log(f'Sold {base_amount} {base_currency}'
                    f'for {base_amount * current_price} {target_currency} '
                    f'( {symbol} -> {current_price} )', print_out)

    if print_out:
        owned_asset = '🚩' if not buy_on_next_trade else '✖'

        if buy_on_next_trade:
            if buy_signal > sell_signal:
                asset_state = '🔼'
            else:
                asset_state = '🔻'
        else:
            if sell_signal > buy_signal:
                asset_state = '🔼'
            else:
                asset_state = '🔻'

        difference_in_percent = 100 * (current_price - last_operation_price) / last_operation_price
        print(f'{owned_asset}\t{asset_state}\t{symbol} \tcp -> {format(current_price, ".3f")}'
            f'{target_currency}\tlop -> {format(last_operation_price, ".3f")} {target_currency}'
            f'\tdif -> {format(difference_in_percent, ".3f")}% | SIGNALS -> {buy_signal}B / '
            f'{sell_signal}S / {total_indicator_count}I')


def get_time_stamp():
    return time.time()

if __name__ == '__main__':

    print_out = False if '--no-print' in sys.argv else True

    # Read the api key and api secret key
    with open(trader.constants.BINANCE_API_KEYS_FILE, 'r') as credentials_file:
        keys = json.loads(credentials_file.read())
        api_key = keys['api_key']
        secret_key = keys['secret_key']

    # Default config values
    default_config = {
        'enabled': True, # if true actively trade with this config, else dismiss
        'base_currency': 'BTC', # First currency asset in the symbol
        'target_currency': 'USDT', # Second currency asset in the symbol, want to maximize this asset
        'buy_on_next_trade': True, # Buy `base_currency` at the next trade
        'trade_amount_buy': 15.0, # Constant amount of `target_currency` to use while buying `base_currency`
        'trade_wealth_percent_sell': 100.0, # The percent of the account balance to be traded while selling `base_currency`
        'last_operation_price': -1.0, # Previous trade price, if there is no trade (-1), set to current price
        'prevent_loss': True, # If True never sell cheaper
    }

    # Fetch config files from fs
    final_config_files = trader.ssb.helper.load_config_file(default_config)

    # Append the individual config files to global var `master_config_files`
    for current_config in final_config_files:
        master_config_files.append(current_config)

    for current_config in master_config_files:
        symbol = current_config['base_currency'] + current_config['target_currency']

        if current_config['last_operation_price'] == -1:
            current_config['last_operation_price'] = trader.binance.trade.get_current_trade_ratio(symbol)

    # Validate the config file
    trader.ssb.helper.validate_config_file(master_config_files)

    # Update config on the file system
    trader.ssb.helper.write_config_file(master_config_files)

    if print_out:
        print(f'Starting the bot with this config:\n\n{json.dumps(master_config_files, indent=4)}\n')

    while True:
        for current_config in master_config_files:
            if current_config['enabled']:
                perform_bot_operations(current_config, api_key, secret_key, print_out) 
        if print_out:
            print('-' * 122)
        time.sleep(5)