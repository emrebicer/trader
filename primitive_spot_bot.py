import sys
import json
import time
import trader.constants
import trader.binance.helper
import trader.binance.trade
import trader.binance.account
import trader.psb.helper

# Keep track of hook and hook price for several symbols in this dictionary
trader_local_data = {}
# Keep track of the individual config files
master_config_files = []


def update_and_save_config_file(config_instance):
    instance_symbol = config_instance['base_currency'] + config_instance['target_currency']

    for current_config_index in range(len(master_config_files)):
        
        current_config = master_config_files[current_config_index]
        current_symbol = current_config['base_currency'] + current_config['target_currency']
        
        if instance_symbol == current_symbol:
            master_config_files[current_config_index] = config_instance
            trader.psb.helper.write_config_file(master_config_files)
            return

    raise Exception(f'The symbol {instance_symbol} was not found in the {master_config_files}')


def perform_bot_operations(config, api_key, secret_key, print_out):
    
    symbol = config['base_currency'] + config['target_currency'] 
    current_price = trader.binance.trade.get_current_trade_ratio(symbol)

    base_currency = config['base_currency']
    target_currency = config['target_currency']
    buy_on_next_trade = config['buy_on_next_trade']
    last_operation_price = config['last_operation_price']
    profit_percent_buy = config['profit_percent_buy']
    profit_percent_sell = config['profit_percent_sell']
    hook_percent = config['hook_percent']
    trade_with_percent_buy = config['trade_with_percent_buy']
    trade_amount_buy = config['trade_amount_buy']
    trade_wealth_percent_buy = config['trade_wealth_percent_buy']
    trade_wealth_percent_sell = config['trade_wealth_percent_sell']
    loss_prevention = config['loss_prevention']
    loss_prevention_percent = config['loss_prevention_percent']
    avoid_buy_on_daily_increase = config['avoid_buy_on_daily_increase']
    avoid_buy_on_daily_increase_percent = config['avoid_buy_on_daily_increase_percent']
    avoid_buy_on_average_increase = config['avoid_buy_on_average_increase']
    avoid_buy_on_average_day_count = config['avoid_buy_on_average_day_count']
    last_trade_time_stamp = config['last_trade_time_stamp']
    update_lop_on_idle = config['update_lop_on_idle']
    update_lop_on_idle_days = config['update_lop_on_idle_days']

    if trader_local_data[symbol]['hook'] and buy_on_next_trade:
        if current_price < trader_local_data[symbol]['hook_price']:
            trader_local_data[symbol]['hook_price'] = current_price
        elif current_price - trader_local_data[symbol]['hook_price'] > (last_operation_price * hook_percent / 100):
            # Create buy order
            if trade_with_percent_buy:
                target_amount = trader.binance.account.get_free_balance_amount(api_key, secret_key, target_currency)
                target_amount = target_amount * trade_wealth_percent_buy / 100
            else:
                target_amount = trade_amount_buy
            quantity = target_amount / current_price
            result = trader.binance.trade.create_market_order(api_key, secret_key, symbol, 'BUY', quantity)
            print(result)
            if result['status'] != 'FILLED':
                print('Response status was not FILLED, won\'t update config...')
                return
            config['last_trade_time_stamp'] = get_time_stamp()
            trader_local_data[symbol]['hook'] = False
            config['buy_on_next_trade'] = False
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)
            trader.psb.helper.log(f'Bought {quantity} {base_currency} for {target_amount} {target_currency} ( {symbol} -> {current_price} )', print_out)

    elif trader_local_data[symbol]['hook'] and not buy_on_next_trade:
        if current_price > trader_local_data[symbol]['hook_price']:
            trader_local_data[symbol]['hook_price'] = current_price
        elif trader_local_data[symbol]['hook_price'] - current_price > (last_operation_price * hook_percent / 100):
            # Create sell order
            base_amount = trader.binance.account.get_free_balance_amount(api_key, secret_key, base_currency)
            # Calculate total amount that we can trade
            base_amount = base_amount * trade_wealth_percent_sell / 100
            result = trader.binance.trade.create_market_order(api_key, secret_key, symbol, 'SELL', base_amount)
            print(result)
            if result['status'] != 'FILLED':
                print('Response status was not FILLED, won\'t update config...')
                return
            config['last_trade_time_stamp'] = get_time_stamp()
            trader_local_data[symbol]['hook'] = False
            config['buy_on_next_trade'] = True
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)
            trader.psb.helper.log(f'Sold {base_amount} {base_currency} for {base_amount * current_price} {target_currency} ( {symbol} -> {current_price} )', print_out)

    elif buy_on_next_trade:
        # Check if the price has decreased by `profit_percent_buy`
        if current_price < last_operation_price - (last_operation_price * profit_percent_buy / 100):
            if avoid_buy_on_daily_increase and trader.binance.helper.get_24hr_price_change_percent(symbol) > avoid_buy_on_daily_increase_percent:
                print(f'Won\'t buy beacuse daily increase percent is {trader.binance.helper.get_24hr_price_change_percent(symbol)}%')
                return
            if avoid_buy_on_average_increase:
                average = trader.binance.helper.get_average_close_ratio(symbol, '1d', avoid_buy_on_average_day_count)
                if current_price > average:
                    print(f'Won\'t buy {symbol}, because average increase is {average} and current price is {current_price}')
                    return
            trader_local_data[symbol]['hook'] = True
            trader_local_data[symbol]['hook_price'] = current_price
            trader.psb.helper.log(f'Hook price -> {current_price}, will buy after hook control ( {symbol} )', print_out)
    else:
        # Check if the price has increased by `profit_percent_sell`
        if current_price > last_operation_price + (last_operation_price * profit_percent_sell / 100):
            trader_local_data[symbol]['hook'] = True
            trader_local_data[symbol]['hook_price'] = current_price
            trader.psb.helper.log(f'Hook price -> {current_price}, will sell after hook control ( {symbol} )', print_out)
        elif loss_prevention:
            # Check for the current loss, if it is over `loss_prevention_percent` set the hook for selling
            if current_price < last_operation_price - (last_operation_price * loss_prevention_percent):
                trader_local_data[symbol]['hook'] = True
                trader_local_data[symbol]['hook_price'] = current_price
                trader.psb.helper.log(f'Loss prevention !!! Hook price -> {current_price}, will sell after hook control ( {symbol} )', print_out)

    # Check if the bot was idle for too long, if so update the lop
    if buy_on_next_trade and update_lop_on_idle and not trader_local_data[symbol]['hook']:
        # Calculate total idle seconds
        idle_seconds = get_time_stamp() - last_trade_time_stamp
        if idle_seconds > update_lop_on_idle_days * 24 * 60 * 60:
            # Stayed idle for too many days, update the last operation price to keep trading
            new_lop = trader.binance.helper.get_average_close_ratio(symbol, '1d', update_lop_on_idle_days)
            if current_price < new_lop:
                # If the current price is lower than the past days average, take it instead
                new_lop = current_price 
            config['last_trade_time_stamp'] = get_time_stamp()
            config['last_operation_price'] = new_lop  
            update_and_save_config_file(config)
            trader.psb.helper.log(f'Update the lop to {new_lop} from {current_price} for {symbol}, because there were no trades within {update_lop_on_idle_days} days', print_out)
                        

    if print_out:
        owned_asset = '🚩' if not buy_on_next_trade else '✖'

        if buy_on_next_trade:
            if current_price < last_operation_price:
                asset_state = '🔼'
            else:
                asset_state = '🔻'
        else:
            if current_price > last_operation_price:
                asset_state = '🔼'
            else:
                asset_state = '🔻'
        
        hook_state = '🎈' if trader_local_data[symbol]['hook'] else ''

        difference_in_percent = 100 * (current_price - last_operation_price) / last_operation_price
        print(f'{owned_asset}\t{asset_state}\t{symbol} \tcp -> {format(current_price, ".3f")} {target_currency}\tlop -> {format(last_operation_price, ".3f")} {target_currency}\tdif -> '
        f'{format(current_price - last_operation_price, ".3f")} {target_currency} ({format(difference_in_percent, ".3f")}%) {hook_state}')


def get_time_stamp():
    return time.time()


if __name__ == '__main__':

    print_out = True
    if '--no-print' in sys.argv:
        print_out = False

    api_key = ''
    secret_key = ''

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
        'last_operation_price': -1.0, # Previous trade price, if there is no trade (-1), set to current price
        'profit_percent_buy': 2.5, # How much should the decrease should be for buying
        'profit_percent_sell': 2.0, # How much should the incease should be for selling 
        'hook_percent': 0.5, # After granting profit, wait until `hook_percent` of loss to ensure to maximize the profit
        'trade_with_percent_buy': True, # Use percent or constant amount of `target_currency` when buying `base_currency`
        'trade_amount_buy': 15.0, # Constant amount of `target_currency` to use while buying `base_currency`
        'trade_wealth_percent_buy': 99.8, # The percent of the account balance to be traded while buying `base_currency`
        'trade_wealth_percent_sell': 100.0, # The percent of the account balance to be traded while selling `base_currency`
        'loss_prevention': False, # Prevent huge loss, sell early (will still lose but avoids a huge loss)
        'loss_prevention_percent': 8.0,
        'avoid_buy_on_daily_increase': True, # Avoid buying `base_currency` if it is pumped daily
        'avoid_buy_on_daily_increase_percent': 5.0,
        'avoid_buy_on_average_increase': True, # Calculate the average of, `day_count` days and don't buy if higher
        'avoid_buy_on_average_day_count': 30,
        'last_trade_time_stamp': -1.0,
        'update_lop_on_idle': True, # If the price went up, will never buy. Update lop after idle `days` to keep trading
        'update_lop_on_idle_days': 3 # How many idle days should the bot wait before updating the price
    }
    
    # Fetch config files from fs
    final_config_files = trader.psb.helper.load_config_file(default_config)
    
    # Append the individual config files to global var `master_config_files`
    for current_config in final_config_files:
        master_config_files.append(current_config)

    for current_config in master_config_files:
        symbol = current_config['base_currency'] + current_config['target_currency']

        if current_config['last_operation_price'] == -1:
            current_config['last_operation_price'] = trader.binance.trade.get_current_trade_ratio(symbol)
        
        if current_config['last_trade_time_stamp'] == -1:
            current_config['last_trade_time_stamp'] = get_time_stamp()

        trader_local_data[symbol] = {'hook': False, 'hook_price': -1}
    
    # Validate the config file
    trader.psb.helper.validate_config_file(master_config_files)
    
    # Update config on the file system
    trader.psb.helper.write_config_file(master_config_files)
    
    if print_out:
        print(f'Starting the bot with this config:\n\n{json.dumps(master_config_files, indent=4)}\n')
    
    while True:
        for current_config in master_config_files:
            if current_config['enabled']:
                try:
                    perform_bot_operations(current_config, api_key, secret_key, print_out) 
                except Exception as ex:
                    symbol = current_config['base_currency'] + current_config['target_currency']
                    trader.psb.helper.error_log(f'Error at perform_bot_operations for: {symbol},'
                        f'Exception message: {ex}', print_out)
        if print_out:
            print('-' * 115)
        time.sleep(5)



