import json
import os
import time
import binance_constants
import binance_helper
import binance_trade
import binance_account

if __name__ == '__main__':
    api_key = ''
    secret_key = ''

    # Read the api key and api secret key
    with open('binance_api_keys.json', 'r') as credentials_file:
        keys = json.loads(credentials_file.read())
        api_key = keys['api_key']
        secret_key = keys['secret_key']

    # Default config values
    config = {
        'base_currency': 'BTC', # First currency in the trade
        'target_currency': 'USDT', # Second currency in the trade
        'buy_on_next_trade': True, # Will buy at the next trade
        'last_operation_price': -1, # Previous trade price, if there is no trade, set to current price
        'profit_percent': 2, # How much should the increase or decrease should be for hooking
        'hook_percent': 0.5, # After granting profit, wait until `hook_percent` of loss to ensure to maximize the profit
        'trade_wealth_percent': 99.8 # The percent of the balance to be traded
    }
    
    # If a config file exists on the fs, load it
    if os.path.isfile(os.path.join(os.getcwd(), binance_constants.CONFIG_FILE)):
        with open(binance_constants.CONFIG_FILE, 'r') as config_file:
            config = json.loads(config_file.read())
    
    if config['last_operation_price'] == -1:
        config['last_operation_price'] = binance_trade.get_current_trade_ratio(config['base_currency'] + config['target_currency'])


    symbol = config['base_currency'] + config['target_currency']
    hook = False
    hook_price = -1

    while True:
        current_price = binance_trade.get_current_trade_ratio(symbol)
        if hook and config['buy_on_next_trade']:
            if current_price < hook_price:
                hook_price = current_price
            elif current_price - hook_price > (config['last_operation_price'] * config['hook_percent'] / 100):
                # Create buy order
                target_amount = binance_account.get_free_balance_amount(api_key, secret_key, config['target_currency'])
                # Calculate total amount that we can trade
                target_amount = target_amount * config['trade_wealth_percent'] / 100
                quantity = target_amount / current_price
                result = binance_trade.create_market_order(api_key, secret_key, symbol, 'BUY', quantity)
                print(result)
                if result['status'] != 'FILLED':
                    print('Response status was not FILLED, won\'t update config...')
                    continue
                hook = False
                config['buy_on_next_trade'] = False
                config['last_operation_price'] = current_price
                binance_helper.update_config_file(config)
                binance_helper.log(f'Bought {quantity} {config["base_currency"]} for {target_amount} {config["target_currency"]} ( {symbol} -> {current_price} )', True)

        elif hook and not config['buy_on_next_trade']:
            if current_price > hook_price:
                hook_price = current_price
            elif hook_price - current_price > (config['last_operation_price'] * config['hook_percent'] / 100):
                # Create sell order
                base_amount = binance_account.get_free_balance_amount(api_key, secret_key, config['base_currency'])
                # Calculate total amount that we can trade
                base_amount = base_amount * config['trade_wealth_percent'] / 100
                result = binance_trade.create_market_order(api_key, secret_key, symbol, 'SELL', base_amount)
                print(result)
                if result['status'] != 'FILLED':
                    print('Response status was not FILLED, won\'t update config...')
                    continue
                hook = False
                config['buy_on_next_trade'] = True
                config['last_operation_price'] = current_price
                binance_helper.update_config_file(config)
                binance_helper.log(f'Sold {base_amount} {config["base_currency"]} for {base_amount * current_price} {config["target_currency"]} ( {symbol} -> {current_price} )', True)

        elif config['buy_on_next_trade']:
            # Check if the price has decreased by `profit_percent`
            if current_price < config['last_operation_price'] - (config['last_operation_price'] * config['profit_percent'] / 100):
                hook = True
                hook_price = current_price
                binance_helper.log(f'Hook price -> {current_price}, will buy after hook control', True)
        else:
            # Check if the price has increased by `profit_percent`
            if current_price > config['last_operation_price'] + (config['last_operation_price'] * config['profit_percent'] / 100):
                hook = True
                hook_price = current_price
                binance_helper.log(f'Hook price -> {current_price}, will sell after hook control', True)


        difference_in_percent = 100 * (current_price - config['last_operation_price']) / config['last_operation_price']
        print(f'cp -> {current_price} {config["target_currency"]}\tlop -> {config["last_operation_price"]} {config["target_currency"]}\tdif -> {int(current_price - config["last_operation_price"])} {config["target_currency"]} ({format(difference_in_percent, ".3f")}%)')

        time.sleep(5)