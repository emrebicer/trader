import os
import requests
import hmac
import decimal
import datetime
import hashlib
import json
import binance_constants


def get_precision_for_symbol(symbol) -> int:
    """ Get the maximum allowed number of decimal points for the given symbol """
    response = requests.get(f'{binance_constants.BASE_ENDPOINT}/api/v3/exchangeInfo')
    response_dict = response.json()
    for info in response_dict['symbols']:
        if info['symbol'] == symbol:
            return int(info['quoteAssetPrecision'])

    raise Exception(f'{symbol} does not exist in the exchange info') 


def update_quantity_according_lot_size_filter(symbol, quantity) -> str:
    """ 
        Update the quantity, make sure it fits in the api restrictions.

        restriction 1 -> quantity % step_size == 0
        restriction 2 -> quantity must have maximum `precision` decimal points
    """
    response = requests.get(f'{binance_constants.BASE_ENDPOINT}/api/v3/exchangeInfo')
    response_dict = response.json()
    for info in response_dict['symbols']:
        if info['symbol'] == symbol:
            filters = info['filters']
            for filter in filters:
                if filter['filterType'] == 'LOT_SIZE':
                    step_size = float(filter['stepSize'])
                    step_size_str = decimal.Context().create_decimal(repr(step_size))
                    step_size_str = format(step_size_str, 'f')
                    # Avoid doing this (even though the logic is correct for all scenarios)
                    # unless step_size ends with 1
                    # Because in small numbers, mod operation returns wrong results
                    # which results in wrong quantity value thus fails the order request
                    if step_size_str[len(step_size_str) - 1] != '1' and quantity % step_size != 0 and quantity % step_size > 0.00000001:
                        quantity -= quantity % step_size

                    # Make sure the quantity is not more precise than the precision
                    precision = get_precision_for_symbol(symbol)
                    quantity_str = str(value_to_decimal(quantity, precision))
                    return quantity_str
    
    raise Exception(f'{symbol} does not exist in the exchange info or LOT_SIZE is not in filters')


def create_signature(secret_key, message):
    """ Create HMAC SHA256 signature """
    # Convert string into byte array
    secret_key = secret_key.encode('utf-8')
    message = message.encode('utf-8')
    # Return generated HMAC SHA256 signature 
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()


def value_to_decimal(value, decimal_places):
    decimal.getcontext().rounding = decimal.ROUND_DOWN
    return decimal.Decimal(str(float(value))).quantize(decimal.Decimal('1e-{}'.format(decimal_places)))

def get_24h_statistics(symbol):

    url = f'{binance_constants.BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}'
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Failed while fetching 24hr statistics for {symbol}')
    
    return response.json()

def get_24hr_price_change_percent(symbol) -> float:
    statistics = get_24h_statistics(symbol)
    if 'priceChangePercent' in statistics:
        return float(statistics['priceChangePercent'])

    raise Exception(f'priceChangePercent was not found in the 24hr statistics for {symbol}')


def get_server_timestamp() -> int:    
    response = requests.get(f'{binance_constants.BASE_ENDPOINT}/api/v3/time')

    if response.status_code != 200:
        raise Exception('Failed while fetching server time')

    return int(response.json()['serverTime'])


def get_klines_data(symbol, interval, limit = 1000):
    accepted_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    
    if interval not in accepted_intervals:
        raise Exception(f'{interval} is not accepted; must be {accepted_intervals}')
    
    if type(limit) is not int:
        raise Exception(f'limit must be an intereger but it was a {type(limit)}')

    if limit > 1000:
        raise Exception(f'limit can not be greater than 1000, it was {limit}')
   
    if limit <= 0:
        raise Exception(f'limit must be a positive integer, it was {limit}')

    target_url = f'{binance_constants.BASE_ENDPOINT}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'

    response = requests.get(target_url)

    if response.status_code != 200:
        raise Exception(f'Failed while fetching klines data')
    
    return response.json()

def get_average_close_ratio(symbol, interval, limit) -> float:
    klines = get_klines_data(symbol, interval, limit)

    total_close_values = 0.0

    for kline in klines:
        total_close_values += float(kline[4])

    return total_close_values / len(klines) 
     

def write_config_file(config):
    with open(binance_constants.CONFIG_FILE, 'w') as config_file:
        config_file.write(json.dumps(config, indent=4))

def fill_empty_fields_with_default_config(current_config, default_config) -> dict:
    if current_config['base_currency'] and current_config['target_currency']:
        symbol = current_config['base_currency'] + current_config['target_currency']
    else:
        symbol = default_config['base_currency'] + default_config['target_currency']
    
    for key in default_config:
        if key not in current_config:
            current_config[key] = default_config[key]
            print(f'Updated `{key}` key in {symbol} config')
    return current_config

def load_config_file(default_config) -> list:
    final_config_files = []

    # If a config file exists on the fs, load it
    if os.path.isfile(os.path.join(os.getcwd(), binance_constants.CONFIG_FILE)):
        with open(binance_constants.CONFIG_FILE, 'r') as config_file:
            saved_config = json.loads(config_file.read())
            if type(saved_config) == dict:
                temp = saved_config
                saved_config = []
                saved_config.append(temp)
            
            for current_config in saved_config:
                final_config_files.append(fill_empty_fields_with_default_config(current_config, default_config))
            
    else:
        # Just start the bot with the default config file
        final_config_files.append(default_config)

    return final_config_files

def log(message, dump_to_console):
    date = datetime.datetime.now()
    log = f'{date} - {message}'
    with open(binance_constants.LOG_FILE, 'a') as log_file:
        log_file.write(f'{log}\n')
    if dump_to_console:
        print(message)

def validate_config_file(config):
    
    if type(config) != list:
        raise Exception(f'Configuration error: the config file must be a list!')
    
    # Make sure each config has a unique symbol
    prev_symbols = []
    for current_config in config:
        current_symbol = current_config['base_currency'] + current_config['target_currency']
        if current_symbol in prev_symbols:
            raise Exception(f'{current_symbol} config duplicate')
        prev_symbols.append(current_symbol)

    expected_config_keys = {
        'base_currency': str,
        'target_currency': str,
        'buy_on_next_trade': bool,
        'last_operation_price': float,
        'profit_percent': float,
        'hook_percent': float,
        'trade_with_percent_buy': bool,
        'trade_amount_buy': float,
        'trade_wealth_percent_buy': float,
        'trade_wealth_percent_sell': float,
        'loss_prevention': bool,
        'loss_prevention_percent': float,
        'avoid_buy_on_daily_increase': bool,
        'avoid_buy_on_daily_increase_percent': float,
        'last_trade_time_stamp': float,
        'update_lop_on_idle': bool, 
        'update_lop_on_idle_days': int 
    }

    # Check if an unknown key exists in the config file
    for current_config in config:
        for key in current_config:
            if key not in expected_config_keys:
                raise Exception(f'{key} was not expected in the config')
    
    for current_config in config:
        for key in expected_config_keys:
            if type(current_config[key]) is not expected_config_keys[key]:
                raise Exception(f'Configuration error: Type of "{key}" must be '
                f'{expected_config_keys[key]}, but it is a {type(current_config[key])}')
