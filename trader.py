from bs4 import BeautifulSoup
import requests
import time

BASE_CURRENCY = 'TRY'
TARGET_CURRENCY = 'EUR'
last_trade_ratio = -1
trade_margin = 0.001
buy_on_next_trade = True

initial_money = 1000
current_money = initial_money

def get_current_ratio() -> float:

    url = f'https://finance.yahoo.com/quote/{TARGET_CURRENCY}{BASE_CURRENCY}%3DX'
    response = BeautifulSoup(requests.get(url).text, 'html.parser')
    return float(response.find('span', class_='Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)').text)

while True:
    current_ratio = get_current_ratio()
    if last_trade_ratio == -1:
        last_trade_ratio = current_ratio
        continue
    print((last_trade_ratio - current_ratio))
    if abs(last_trade_ratio - current_ratio) > trade_margin:
        if buy_on_next_trade and current_ratio < last_trade_ratio:
            # Buy
            current_money = current_money / current_ratio
            buy_on_next_trade = not buy_on_next_trade
            last_trade_ratio = current_ratio
            print('-------------------------------------------------')
            print(f'Bought {TARGET_CURRENCY} at {current_ratio} ratio ({time.strftime("%H:%M:%S", time.localtime())})')
            print(f'Current money: {current_money:.2f} {TARGET_CURRENCY}')
        elif not buy_on_next_trade and current_ratio > last_trade_ratio:
            # Sell
            current_money = current_money * current_ratio
            buy_on_next_trade = not buy_on_next_trade
            last_trade_ratio = current_ratio
            print('-------------------------------------------------')
            print(f'Bought {BASE_CURRENCY} at {current_ratio} ratio ({time.strftime("%H:%M:%S", time.localtime())})')
            print(f'Current money: {current_money:.2f} {BASE_CURRENCY}')

    
    time.sleep(2)
