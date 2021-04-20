import requests
import hmac
import decimal
import hashlib
import datetime
import constants


def get_precision_for_symbol(symbol) -> int:
    """ Get the maximum allowed number of decimal points for the given symbol """
    response = requests.get(f'{constants.BASE_ENDPOINT}/api/v3/exchangeInfo')
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
    response = requests.get(f'{constants.BASE_ENDPOINT}/api/v3/exchangeInfo')
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

                    step_size_prec = 0
                    for ch in step_size_str:
                        if ch == '.':
                            continue
                        elif ch != '0':
                            break
                        else:
                            step_size_prec += 1

                    # Make sure the quantity is not more precise than the precision
                    precision = get_precision_for_symbol(symbol)
                    target_precision = min(precision, step_size_prec)
                    quantity_str = str(value_to_decimal(quantity, target_precision))
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

    url = f'{constants.BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}'
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
    response = requests.get(f'{constants.BASE_ENDPOINT}/api/v3/time')

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

    target_url = f'{constants.BASE_ENDPOINT}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'

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

def get_rsi(symbol, time_frame, moving_average = 0, data_count = 14) -> float:
    """
        Returns Relative Strength Index

        moving_average
            0 - SMA (Simple Moving Average)
            1 - EMA (Exponential Moving Average)
    """

    # Fetch <data_count + 1> days to calculate the change on <data_count> days
    klines = get_klines_data(symbol, time_frame, data_count + 1)

    change_up = []
    change_down = []

    if len(klines) == 0:
        return 0

    for index in range(1, len(klines)):

        current_close = float(klines[index][4])
        prev_close = float(klines[index - 1][4])

        diff = current_close - prev_close

        if diff > 0:
            change_up.append(diff)
            change_down.append(0)
        else:
            change_down.append(-diff)
            change_up.append(0)

    up_avg = sum(change_up) / len(change_up)
    down_avg = sum(change_down) / len(change_down)

    if moving_average == 0:
        rs = up_avg / down_avg 
        return 100 - (100 / (1 + rs))

    elif moving_average == 1:
        a = 2 / ( data_count + 1 )
        for index in range(0, len(change_up)):
            up_avg = a * change_up[index] + (1 - a) * up_avg 

        for index in range(0, len(change_down)):
            down_avg = a * change_down[index] + (1 - a) * down_avg 

        rs = up_avg / down_avg 
        rsi = 100 - (100 / ( 1 + rs))
        return rsi
    
    else:
        raise Exception(f'<{moving_average}> is not valid for moving average parameter')

def log(filename, message, dump_to_console):
    date = datetime.datetime.now()
    log = f'{date} - {message}'
    with open(filename, 'a') as log_file:
        log_file.write(f'{log}\n')
    if dump_to_console:
        print(message)

def error_log(filename, message, dump_to_console):
    log(filename, message, dump_to_console)