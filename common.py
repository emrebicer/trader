from bs4 import BeautifulSoup
import requests

def get_average_ratio(days, base_currency, target_currency) -> float:
    """
        Calculate the Simple moving average (SMA) for
        given days before now based on base and target currency
    """
    url = f'https://finance.yahoo.com/quote/{target_currency}{base_currency}%3DX/history?p={target_currency}{base_currency}%3DX'
    response = None
    response = BeautifulSoup(requests.get(url).text, 'html.parser')
    table = response.find('tbody').findAll('tr')
    table = table if len(table) <= days else table[:days]
    if len(table) != days:
        print(f'Warning: this is the average rate for {len(table)} instead of {days}, could not fecth enough data.')
    total = 0.0
    for data in table:
        cells = data.findAll("td")
        #print(f'{cells[0].text} -> {cells[4].text}')
        total += float(cells[4].text.replace(',', ''))
    return total / float(len(table))

def get_current_ratio(base_currency, target_currency) -> float:
    """
        Get the current exchange ratio between
        two currency
    """
    url = f'https://finance.yahoo.com/quote/{target_currency}{base_currency}%3DX'
    response = BeautifulSoup(requests.get(url).text, 'html.parser')
    return float(response.find('span', class_='Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)').text.replace(',', ''))

def get_current_trade_ratio_eur_try(buy_eur = True) -> float:
    """
        Current buy and sell exchange ratio on 
        iş-bank for only EUR and TRY exchange
    """
    url = f'https://www.isbank.com.tr/doviz-kurlari'
    response = BeautifulSoup(requests.get(url).text, 'html.parser')
    eur_row = response.find('tr', id='ctl00_ctl08_g_1e38731d_affa_44fc_85c6_ae10fda79f73_ctl00_FxRatesRepeater_ctl01_fxItem')
    ratio = eur_row.findAll('td')
    return float(ratio[1 if not buy_eur else 2].text.replace('\n', '').replace(' ', '').replace(',', '.'))

