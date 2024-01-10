import requests
import trader.binance.helper
import trader.constants


def get_current_trade_ratio(symbol) -> float:
    response = requests.get(f'{trader.constants.BASE_ENDPOINT}/api/v3/ticker/24hr?symbol={symbol}')

    if response.status_code != 200:
        raise Exception(f'Failed to fetch trade ratio, response: {response.text}')

    response_dict = response.json()
    if 'lastPrice' not in response_dict:
        raise Exception('Response does not include `lastPrice` value')

    return float(response_dict['lastPrice'])


def create_limit_order(api_key, secret_key, symbol, side, quantity, price) -> dict:
    quantity_str = trader.binance.helper.update_quantity_according_lot_size_filter(symbol, quantity)
    price = get_current_trade_ratio(symbol)
    timestamp = trader.binance.helper.get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=LIMIT&timestamp={timestamp}&quantity={quantity_str}&price={price}&timeInForce=GTC'
    signature = trader.binance.helper.create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{trader.constants.BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        raise Exception(f'Failed to post -> create_limit_order, response: {response.text}')
    return response.json()


def create_market_order(api_key, secret_key, symbol, side, quantity) -> dict:
    """ Buy instantly at the current price """
    quantity_str = trader.binance.helper.update_quantity_according_lot_size_filter(symbol, quantity)
    timestamp = trader.binance.helper.get_server_timestamp()
    total_params = f'symbol={symbol}&side={side}&type=MARKET&timestamp={timestamp}&quantity={quantity_str}'
    signature = trader.binance.helper.create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.post(f'{trader.constants.BASE_ENDPOINT}/api/v3/order?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        raise Exception(f'Failed to post -> create_market_order, response: {response.text}')
    return response.json()
