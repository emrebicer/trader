import datetime
import requests
import json
import hmac
import hashlib

BASE_ENDPOINT = 'https://api2.binance.com'
LOG_FILE = 'binance_log.txt'


def log(message):
    date = datetime.datetime.now()
    log = f'{date} - {message}'
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f'\n{log}')


def get_current_trade_ratio(symbol) -> float:
    response = requests.get(f'{BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}')

    if response.status_code != 200:
        raise Exception('Failed to fetch trade ratio')

    response_dict = response.json()
    if 'lastPrice' not in response_dict:
        raise Exception('Response does not include `lastPrice` value')

    return response_dict['lastPrice']
    


def create_order(api_key, secret_key, symbol, side, order_type):

    price = get_current_trade_ratio(symbol)
    timestamp = get_server_timestamp()
    quantity = 1
    total_params = f'symbol={symbol}&side={side}&type={order_type}&timestamp={timestamp}&quantity={quantity}&price={price}&timeInForce=GTC'
    signature = create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{BASE_ENDPOINT}/api/v3/order/test?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> create_order')
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
        raise Exception('Failed to post -> create_order')
        return
    return response.json()    



def create_signature(secret_key, message):
    """ Create HMAC SHA256 signature """
    # Convert string into byte array
    secret_key = secret_key.encode('utf-8')
    message = message.encode('utf-8')
    # Return generated HMAC SHA256 signature 
    return hmac.new(secret_key, message, hashlib.sha256).hexdigest()


def get_server_timestamp():
    return int(datetime.datetime.now().timestamp() * 1000) - 2000


api_key = ''
secret_key = ''

with open('binance_api_keys.json', 'r') as credentials_file:
    keys = json.loads(credentials_file.read())
    api_key = keys['api_key']
    secret_key = keys['secret_key']


#print(get_current_trade_ratio('BTCUSDT'))
#print(get_account_information(api_key, secret_key))
print(create_order(api_key, secret_key, 'BTCUSDT', "BUY", "LIMIT"))