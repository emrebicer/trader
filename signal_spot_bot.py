import argparse
import json
import time

import trader.binance.account
import trader.binance.helper
import trader.binance.indicators
import trader.binance.trade
import trader.constants
import trader.helper
import trader.ssb.constants
import trader.ssb.helper

from tui.ssb_interface import TUI, LiveDataInfo

# Keep track of the individual config files
master_config_files = []

# Telegram user to be notified on buy or sell
telegram_chat_id = ''
telegram_api_token = ''

# Discord channel to be notified on buy or sell
discord_channel_id = ''
discord_api_token = ''

# If prevent_loss is enabled,
# make sure the profit is at least <MIN_PROFIT_PERCENT>
MIN_PROFIT_PERCENT = 6

BUY_SIGNAL_PERCENT = 100
SELL_SIGNAL_PERCENT = 80 

BUY_SIGNAL_EMOJI = '💸'
SELL_SIGNAL_EMOJI = '🔔'

# For syncing with the TUI
live_data_points = {}

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

def is_telegram_enabled():
    return telegram_chat_id != '' and telegram_api_token != ''

def is_discord_enabled():
    return discord_channel_id != '' and discord_api_token != ''

def perform_bot_operations(config, api_key, secret_key, tui):

    base_currency = config['base_currency']
    target_currency = config['target_currency']
    buy_on_next_trade = config['buy_on_next_trade']
    trade_amount_buy = config['trade_amount_buy']
    trade_wealth_percent_sell = config['trade_wealth_percent_sell']
    last_operation_price = config['last_operation_price']
    prevent_loss = config['prevent_loss']

    symbol = base_currency + target_currency
    current_price = trader.binance.trade.get_current_trade_ratio(symbol)

    total_indicator_count = 5
    # Check the indicator signals
    buy_signal = 0
    sell_signal = 0

    # RSI indicator
    rsi_margin = 4.0
    rsi = trader.binance.indicators.get_rsi(symbol, '4h', moving_average=0, data_count=14)
    if rsi >= 70 - rsi_margin:
        sell_signal += 1
    elif rsi <= 30 + rsi_margin:
        buy_signal += 1

    # Bollinger bands indicator
    (upper, _, lower) = trader.binance.indicators.get_bollinger_bands(symbol, '4h', 20)

    if current_price > upper:
        sell_signal += 1
    elif current_price < lower:
        buy_signal += 1

    # Simple moving average
    sma = trader.binance.indicators.get_sma(symbol, '4h', 9)
    if current_price > sma:
        sell_signal += 1
    elif current_price < sma:
        buy_signal += 1

    # Exponential moving average (4h)
    ema = trader.binance.indicators.get_ema(symbol, '4h', 9)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1

    # Exponential moving average (1d)
    ema = trader.binance.indicators.get_ema(symbol, '1d', 9)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1

    if buy_on_next_trade:
        current_buy_signal_percent = 100 * buy_signal / total_indicator_count
        if current_buy_signal_percent >= BUY_SIGNAL_PERCENT:
            target_amount = trade_amount_buy
            quantity = target_amount / current_price
            result = trader.binance.trade.create_market_order(
                api_key,
                secret_key,
                symbol,
                'BUY',
                quantity
            )
            if result['status'] != 'FILLED':
                err_log = f"Response status was't FILLED, could't create BUY order for {symbol}"
                trader.ssb.helper.error_log(err_log, False)
                tui.program_log.add_log(err_log)
                return

            config['buy_on_next_trade'] = False
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)

            if 'executedQty' in result.keys():
                quantity = result['executedQty']
            if 'cummulativeQuoteQty' in result.keys():
                target_amount = result['cummulativeQuoteQty']

            log_str = f'Bought {quantity} {base_currency} for {target_amount} '\
                f'{target_currency} ( {symbol} -> {current_price} )'
            trader.ssb.helper.log(log_str, False)
            tui.transaction_log.add_log(log_str)

            if is_telegram_enabled():
                trader.helper.notify_on_telegram(
                    telegram_api_token,
                    telegram_chat_id,
                    log_str
                )

            if is_discord_enabled():
                trader.helper.notify_on_discord(
                    discord_api_token,
                    discord_channel_id,
                    log_str
                )
    else:
        current_sell_signal_percent = 100 * sell_signal / total_indicator_count
        if current_sell_signal_percent >= SELL_SIGNAL_PERCENT:
            # If prevent_loss is enabled,
            # make sure the profit is at least <MIN_PROFIT_PERCENT>
            if (not prevent_loss) or (prevent_loss and (current_price >= last_operation_price + (last_operation_price * MIN_PROFIT_PERCENT / 100))):
                # Create sell order
                base_amount = trader.binance.account.get_free_balance_amount(
                    api_key,
                    secret_key,
                    base_currency
                )
                # Calculate total amount that we can trade
                base_amount = base_amount * trade_wealth_percent_sell / 100
                result = trader.binance.trade.create_market_order(
                    api_key,
                    secret_key,
                    symbol,
                    'SELL',
                    base_amount
                )

                if result['status'] != 'FILLED':
                    err_log = f"Response status was't FILLED, could't create SELL order for {symbol}"
                    trader.ssb.helper.error_log(err_log, False)
                    tui.program_log.add_log(err_log)
                    return

                if 'executedQty' in result.keys():
                    quantity = result['executedQty']
                else:
                    quantity = base_amount
                if 'cummulativeQuoteQty' in result.keys():
                    target_amount = result['cummulativeQuoteQty']
                else:
                    target_amount = quantity * current_price

                config['buy_on_next_trade'] = True
                config['last_operation_price'] = current_price
                update_and_save_config_file(config)
                log_str = f'Sold {quantity} {base_currency} '\
                    f'for {target_amount} {target_currency} '\
                    f'( {symbol} -> {current_price} )'

                trader.ssb.helper.log(log_str, False)
                tui.transaction_log.add_log(log_str)

                if is_telegram_enabled() or is_discord_enabled():
                    try:
                        profit_text = get_sell_profit_text(
                            base_currency,
                            target_currency,
                            target_amount
                        )
                    except Exception as ex:
                        err_log = f'Error at get_sell_profit_text, Exception message: {ex}'
                        trader.ssb.helper.error_log(err_log, False)
                        tui.program_log.add_log(err_log)
                        profit_text = ''

                    notification_str = f'{log_str} {profit_text}'

                    if is_telegram_enabled():
                        trader.helper.notify_on_telegram(
                            telegram_api_token,
                            telegram_chat_id,
                            notification_str
                         )

                    if is_discord_enabled():
                        trader.helper.notify_on_discord(
                            discord_api_token,
                            discord_channel_id,
                            notification_str
                        )

    owned_asset = '🚩 true' if not buy_on_next_trade else '➖ false'

    if buy_on_next_trade:
        if buy_signal > sell_signal:
            is_in_favor = True
        else:
            is_in_favor = False
    else:
        if sell_signal > buy_signal:
            is_in_favor = True
        else:
            is_in_favor = False

    difference_in_percent = 100 * (current_price - last_operation_price) / last_operation_price

    live_data_points[f'{symbol}'] = LiveDataInfo(not buy_on_next_trade, base_currency, target_currency, is_in_favor, current_price, last_operation_price, difference_in_percent, f'{buy_signal} Buy - {sell_signal} Sell {BUY_SIGNAL_EMOJI * buy_signal}{SELL_SIGNAL_EMOJI * sell_signal}')
    tui.live_data.update_data_points(live_data_points.copy())

def get_sell_profit_text(base_currency, target_currency, target_amount) -> str:
    symbol = base_currency + target_currency
    difference = calculate_sell_profit(symbol, target_amount)
    if difference == 0:
        return ""

    if difference > 0:
        return f'(Profit: {difference} {target_currency})'
    else:
        return f'(Loss: {difference} {target_currency})'

def calculate_sell_profit(symbol, target_amount) -> float:
    # Get the latest bought log for <symbol>
    with open(trader.ssb.constants.LOG_FILE, 'r') as log_file:
        logs = [log for log in log_file.readlines() if symbol in log and 'Bought' in log]
        if len(logs) == 0:
            return 0.0

        last_bought_log = logs[-1]
        last_bought_target_quantity = float(last_bought_log.split(' ')[4])
        target_amount = float(target_amount)
        return target_amount - last_bought_target_quantity

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description = 'A bot that does cryptocurrency trading based on several indicator signals.')
    parser.add_argument('-t',
                        '--telegram',
                        help = 'The telegram chat_id that will be notified on buy or sell operations.',
                        type = str,
                        default = '',
                    )

    parser.add_argument('-d',
                        '--discord',
                        help = 'The discord channel_id that will be notified on buy or sell operations.',
                        type = str,
                        default = '',
                    )

    args = parser.parse_args()
    telegram_chat_id = args.telegram
    discord_channel_id = args.discord

    tui = TUI()
    tui.nonblocking_draw()

    tui.program_log.add_log("Started the trader bot!")

    # Read the binance api key and api secret key
    with open(trader.constants.BINANCE_API_KEYS_FILE, 'r') as credentials_file:
        keys = json.loads(credentials_file.read())
        api_key = keys['api_key']
        secret_key = keys['secret_key']

    if telegram_chat_id != '':
        # Read the telegram api token
        with open(trader.constants.TELEGRAM_BOT_API_KEYS_FILE, 'r') as credentials_file:
            keys = json.loads(credentials_file.read())
            telegram_api_token = keys['api_token']

    if discord_channel_id != '':
        # Read the discord api token
        with open(trader.constants.DISCORD_BOT_API_KEYS_FILE, 'r') as credentials_file:
            keys = json.loads(credentials_file.read())
            discord_api_token = keys['api_token']

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

    while True:
        for current_config in master_config_files:
            print(current_config)
            if current_config['enabled']:
                try:
                    perform_bot_operations(current_config, api_key, secret_key, tui) 
                except Exception as ex:
                    symbol = current_config['base_currency'] + current_config['target_currency']
                    err_log = f'Error at perform_bot_operations for: {symbol}, Exception message: {ex}'
                    trader.ssb.helper.error_log(err_log, False)
                    tui.program_log.add_log(err_log)

        time.sleep(5)
