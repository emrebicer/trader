import requests
import binance_helper
import binance_constants


def get_current_trade_ratio(symbol) -> float:
    response = requests.get(f'{binance_constants.BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}')

    if response.status_code != 200:
        raise Exception('Failed to fetch trade ratio')

    response_dict = response.json()
    if 'lastPrice' not in response_dict:
        raise Exception('Response does not include `lastPrice` value')

    return float(response_dict['lastPrice'])


def create_limit_order(api_key, secret_key, symbol, side, quantity, price) -> dict:
    quantity_str = binance_helper.update_quantity_according_lot_size_filter(symbol, quantity)
    price = get_current_trade_ratio(symbol)
    timestamp = binance_helper.get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=LIMIT&timestamp={timestamp}&quantity={quantity_str}&price={price}&timeInForce=GTC'
    signature = binance_helper.create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{binance_constants.BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> create_limit_order')
    return response.json()


def create_market_order(api_key, secret_key, symbol, side, quantity) -> dict:
    """ Buy instantly at the current price """
    quantity_str = binance_helper.update_quantity_according_lot_size_filter(symbol, quantity)
    timestamp = binance_helper.get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=MARKET&timestamp={timestamp}&quantity={quantity_str}'
    signature = binance_helper.create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{binance_constants.BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> create_market_order')
    return response.json()