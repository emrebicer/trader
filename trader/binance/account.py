import requests
import trader.binance.helper
import trader.constants


def get_account_information(api_key, secret_key) -> dict:
    timestamp = trader.binance.helper.get_server_timestamp()
    total_params = f'timestamp={timestamp}'
    signature = trader.binance.helper.create_signature(secret_key, total_params)
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.get(f'{trader.constants.BASE_ENDPOINT}/api/v3/account?{total_params}&signature={signature}', headers = headers)

    if response.status_code != 200:
        print(response.json())
        raise Exception('Failed to post -> get_account_information')
    return response.json()


def get_free_balance_amount(api_key, secret_key, currency) -> float:
    """ Returns available free balance in the account """
    info = get_account_information(api_key, secret_key)
    balances = info['balances']
    for balance in balances:
        if balance['asset'] == currency:
            return float(balance['free'])
            
    raise Exception(f'{currency} does not exist in the balance info')