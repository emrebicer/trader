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
                    if quantity % step_size == 0:
                        return quantity
                    else:
                        quantity -= (quantity % step_size)
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



def update_config_file(config):
    with open(binance_constants.CONFIG_FILE, 'w') as config_file:
        config_file.write(json.dumps(config, indent=4))


def log(message, dump_to_console):
    date = datetime.datetime.now()
    log = f'{date} - {message}'
    with open(binance_constants.LOG_FILE, 'a') as log_file:
        log_file.write(f'{log}\n')
    if dump_to_console:
        print(message)

def validate_config_file(config):

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
        'avoid_buy_on_daily_increase_percent': float
    }

    for key in expected_config_keys:
        if type(config[key]) is not expected_config_keys[key]:
            raise Exception(f'Configuration error: Type of "{key}" must be '
            f'{expected_config_keys[key]}, but it is a {type(config[key])}')
