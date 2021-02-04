import datetime
import requests
import json
import hmac
import hashlib
import os
import time

BASE_ENDPOINT = 'https://api2.binance.com'
LOG_FILE = 'binance_log.txt'
CONFIG_FILE = 'binance_trader_config.json'


def get_current_trade_ratio(symbol) -> float:
    response = requests.get(f'{BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}')

    if response.status_code != 200:
        raise Exception('Failed to fetch trade ratio')

    response_dict = response.json()
    if 'lastPrice' not in response_dict:
        raise Exception('Response does not include `lastPrice` value')

    return float(response_dict['lastPrice'])


def create_limit_order(api_key, secret_key, symbol, side, quantity, price):
    price = get_current_trade_ratio(symbol)
    timestamp = get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=LIMIT&timestamp={timestamp}&quantity={quantity}&price={price}&timeInForce=GTC'
    signature = create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> create_limit_order')
        return
    return response.json()


def create_market_order(api_key, secret_key, symbol, side, quantity):
    """ Buy instantly at the current price """
    timestamp = get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=MARKET&timestamp={timestamp}&quantity={quantity}'
    signature = create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> create_market_order')
        return
    return response.json()
    

def get_account_information(api_key, secret_key):
    timestamp = get_server_timestamp()
    total_params = f'timestamp={timestamp}'
    signature = create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.get(f'{BASE_ENDPOINT}/api/v3/account?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> get_account_information')
        return
    return response.json()    


def get_free_balance_amount(api_key, secret_key, currency):
    """ Returns available free balance in the account """
    info = get_account_information(api_key, secret_key)
    balances = info['balances']
    for balance in balances:
        if balance['asset'] == currency:
            return float(balance['free'])
            
    raise Exception(f'{currency} does not exist in the balance info')


def create_signature(secret_key, message):
    """ Create HMAC SHA256 signature """
    # Convert string into byte array
    secret_key = secret_key.encode('utf-8')
    message = message.encode('utf-8')
    # Return generated HMAC SHA256 signature 
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()


def get_server_timestamp():
    return int(datetime.datetime.now().timestamp() * 1000) - 2000


def update_config_file(config):
    with open(CONFIG_FILE, 'w') as config_file:
        config_file.write(json.dumps(config))


def log(message, dump_to_console):
    date = datetime.datetime.now()
    log = f'{date} - {message}'
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f'\n{log}')
    if dump_to_console:
        print(message)

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
    config['last_operation_price'] = get_current_trade_ratio(config['base_currency'] + config['target_currency'])
    
    # If a config file exists on the fs, load it
    if os.path.isfile(os.path.join(os.getcwd(), CONFIG_FILE)):
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.loads(config_file.read())    

    symbol = config['base_currency'] + config['target_currency']
    hook = False
    hook_price = -1

    while True:
        current_price = get_current_trade_ratio(symbol)
        if hook and config['buy_on_next_trade']:
            if current_price < hook_price:
                hook_price = current_price
            elif current_price - hook_price > (config['last_operation_price'] * config['hook_percent'] / 100):
                # Create buy order
                target_amount = get_free_balance_amount(api_key, secret_key, config['target_currency'])
                # Calculate total amount that we can trade
                target_amount = target_amount * config['trade_wealth_percent'] / 100
                quantity = target_amount / current_price
                result = create_market_order(api_key, secret_key, symbol, 'BUY', quantity)
                print(result)
                if result['status'] != 'FILLED':
                    print('Response status was not filled, won\'t update config...')
                    continue
                hook = False
                config['buy_on_next_trade'] = False
                config['last_operation_price'] = current_price
                update_config_file(config)
                log(f'Bought {quantity} {config["base_currency"]} for {target_amount} {config["target_currency"]} ( {symbol} -> {current_price} )', True)

        elif hook and not config['buy_on_next_trade']:
            if current_price > hook_price:
                hook_price = current_price
            elif hook_price - current_price > (config['last_operation_price'] * config['hook_percent'] / 100):
                # Create sell order
                base_amount = get_free_balance_amount(api_key, secret_key, config['base_currency'])
                # Calculate total amount that we can trade
                base_amount = base_amount * config['trade_wealth_percent'] / 100
                result = create_market_order(api_key, secret_key, symbol, 'SELL', base_amount)
                print(result)
                if result['status'] != 'FILLED':
                    print('Response status was not filled, won\'t update config...')
                    continue
                hook = False
                config['buy_on_next_trade'] = True
                config['last_operation_price'] = current_price
                update_config_file(config)
                log(f'Sold {base_amount} {config["base_currency"]} for {base_amount * current_price} {config["target_currency"]} ( {symbol} -> {current_price} )', True)

        elif config['buy_on_next_trade']:
            # Check if the price has decreased by `profit_percent`
            if current_price < config['last_operation_price'] - (config['last_operation_price'] * config['profit_percent'] / 100):
                hook = True
                hook_price = current_price
                log(f'Hook price -> {current_price}, will buy after hook control', True)
        else:
            # Check if the price has increased by `profit_percent`
            if current_price > config['last_operation_price'] + (config['last_operation_price'] * config['profit_percent'] / 100):
                hook = True
                hook_price = current_price
                log(f'Hook price -> {current_price}, will sell after hook control', True)


        difference_in_percent = 100 * (current_price - config['last_operation_price']) / config['last_operation_price']
        print(f'cp -> {current_price} {config["target_currency"]}\tlop -> {config["last_operation_price"]} {config["target_currency"]}\tdif -> {int(current_price - config["last_operation_price"])} {config["target_currency"]} ({format(difference_in_percent, ".3f")}%)')

        time.sleep(5)