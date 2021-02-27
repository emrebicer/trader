import json
import time
import os
import sys
import time
import binance_constants
import binance_helper
import binance_trade
import binance_account

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
            binance_helper.write_config_file(master_config_files)
            return

    raise Exception(f'The symbol {instance_symbol} was not found in the {master_config_files}')


def perform_bot_operations(config, api_key, secret_key, print_out):
    
    symbol = config['base_currency'] + config['target_currency'] 
    current_price = binance_trade.get_current_trade_ratio(symbol)
    
    if trader_local_data[symbol]['hook'] and config['buy_on_next_trade']:
        if current_price < trader_local_data[symbol]['hook_price']:
            trader_local_data[symbol]['hook_price'] = current_price
        elif current_price - trader_local_data[symbol]['hook_price'] > (config['last_operation_price'] * config['hook_percent'] / 100):
            # Create buy order
            if config['trade_with_percent_buy']:
                target_amount = binance_account.get_free_balance_amount(api_key, secret_key, config['target_currency'])
                target_amount = target_amount * config['trade_wealth_percent_buy'] / 100
            else:
                target_amount = config['trade_amount_buy']
            quantity = target_amount / current_price
            result = binance_trade.create_market_order(api_key, secret_key, symbol, 'BUY', quantity)
            print(result)
            if result['status'] != 'FILLED':
                print('Response status was not FILLED, won\'t update config...')
                return
            config['last_trade_time_stamp'] = get_time_stamp()
            trader_local_data[symbol]['hook'] = False
            config['buy_on_next_trade'] = False
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)
            binance_helper.log(f'Bought {quantity} {config["base_currency"]} for {target_amount} {config["target_currency"]} ( {symbol} -> {current_price} )', print_out)

    elif trader_local_data[symbol]['hook'] and not config['buy_on_next_trade']:
        if current_price > trader_local_data[symbol]['hook_price']:
            trader_local_data[symbol]['hook_price'] = current_price
        elif trader_local_data[symbol]['hook_price'] - current_price > (config['last_operation_price'] * config['hook_percent'] / 100):
            # Create sell order
            base_amount = binance_account.get_free_balance_amount(api_key, secret_key, config['base_currency'])
            # Calculate total amount that we can trade
            base_amount = base_amount * config['trade_wealth_percent_sell'] / 100
            result = binance_trade.create_market_order(api_key, secret_key, symbol, 'SELL', base_amount)
            print(result)
            if result['status'] != 'FILLED':
                print('Response status was not FILLED, won\'t update config...')
                return
            config['last_trade_time_stamp'] = get_time_stamp()
            trader_local_data[symbol]['hook'] = False
            config['buy_on_next_trade'] = True
            config['last_operation_price'] = current_price
            update_and_save_config_file(config)
            binance_helper.log(f'Sold {base_amount} {config["base_currency"]} for {base_amount * current_price} {config["target_currency"]} ( {symbol} -> {current_price} )', print_out)

    elif config['buy_on_next_trade']:
        # Check if the price has decreased by `profit_percent`
        if current_price < config['last_operation_price'] - (config['last_operation_price'] * config['profit_percent'] / 100):
            if config['avoid_buy_on_daily_increase'] and binance_helper.get_24hr_price_change_percent(symbol) > config['avoid_buy_on_daily_increase_percent']:
                print(f'Won\'t buy beacuse daily increase percent is {binance_helper.get_24hr_price_change_percent(symbol)}%')
                return
            trader_local_data[symbol]['hook'] = True
            trader_local_data[symbol]['hook_price'] = current_price
            binance_helper.log(f'Hook price -> {current_price}, will buy after hook control', print_out)
    else:
        # Check if the price has increased by `profit_percent`
        if current_price > config['last_operation_price'] + (config['last_operation_price'] * config['profit_percent'] / 100):
            trader_local_data[symbol]['hook'] = True
            trader_local_data[symbol]['hook_price'] = current_price
            binance_helper.log(f'Hook price -> {current_price}, will sell after hook control', print_out)
        elif config['loss_prevention']:
            # Check for the current loss, if it is over `loss_prevention_percent` set the hook for selling
            if current_price < config['last_operation_price'] - (config['last_operation_price'] * config['loss_prevention_percent']):
                trader_local_data[symbol]['hook'] = True
                trader_local_data[symbol]['hook_price'] = current_price
                binance_helper.log(f'Loss prevention !!! Hook price -> {current_price}, will sell after hook control', print_out)

    if print_out:
        difference_in_percent = 100 * (current_price - config['last_operation_price']) / config['last_operation_price']
        print(f'{symbol} cp -> {current_price} {config["target_currency"]}\tlop -> {config["last_operation_price"]} {config["target_currency"]}\tdif -> {int(current_price - config["last_operation_price"])} {config["target_currency"]} ({format(difference_in_percent, ".3f")}%)')


def get_time_stamp():
    return time.time()


if __name__ == '__main__':

    print_out = True
    if '--no-print' in sys.argv:
        print_out = False

    api_key = ''
    secret_key = ''

    # Read the api key and api secret key
    with open('binance_api_keys.json', 'r') as credentials_file:
        keys = json.loads(credentials_file.read())
        api_key = keys['api_key']
        secret_key = keys['secret_key']

    # Default config values
    default_config = {
        'base_currency': 'BTC', # First currency in the trade
        'target_currency': 'USDT', # Second currency in the trade, want to maximize this asset
        'buy_on_next_trade': True, # Buy `base_currency` at the next trade
        'last_operation_price': -1.0, # Previous trade price, if there is no trade (-1), set to current price
        'profit_percent': 2.0, # How much should the increase or decrease should be for hooking
        'hook_percent': 0.5, # After granting profit, wait until `hook_percent` of loss to ensure to maximize the profit
        'trade_with_percent_buy': True, # Use percent or constant amount of `target_currency` when buying `base_currency`
        'trade_amount_buy': 15.0, # Constant amount of `target_currency` to use while buying `base_currency`
        'trade_wealth_percent_buy': 99.8, # The percent of the account balance to be traded while buying `base_currency`
        'trade_wealth_percent_sell': 100.0, # The percent of the account balance to be traded while selling `base_currency`
        'loss_prevention': False, # Prevent huge loss, sell early (will still lose but avoids a huge loss)
        'loss_prevention_percent': 8.0,
        'avoid_buy_on_daily_increase': True, # Avoid buying `base_currency` if it is pumped daily
        'avoid_buy_on_daily_increase_percent': 5.0,
        'last_trade_time_stamp': -1.0
    }
    
    # Fetch config files from fs
    final_config_files = binance_helper.load_config_file(default_config)
    
    # Append the individual config files to global var `master_config_files`
    for current_config in final_config_files:
        master_config_files.append(current_config)

    for current_config in master_config_files:
        symbol = current_config['base_currency'] + current_config['target_currency']

        if current_config['last_operation_price'] == -1:
            current_config['last_operation_price'] = binance_trade.get_current_trade_ratio(symbol)
        
        if current_config['last_trade_time_stamp'] == -1:
            current_config['last_trade_time_stamp'] = get_time_stamp()

        trader_local_data[symbol] = {'hook': False, 'hook_price': -1}
    
    # Validate the config file
    binance_helper.validate_config_file(master_config_files)
    
    # Update config on the file system
    binance_helper.write_config_file(master_config_files)
    
    if print_out:
        print(f'Starting the bot with this config:\n\n{json.dumps(master_config_files, indent=4)}\n')
    
    while True:
        for current_config in master_config_files:
            perform_bot_operations(current_config, api_key, secret_key, print_out) 
        if print_out:
            print('---------------------------------------------------------------------------------')
        time.sleep(5)



