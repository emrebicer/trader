from binance_helper import get_24h_statistics
from binance_helper import get_24hr_price_change_percent 

symbol = "DOGEUSDT"

daily_statistics = get_24h_statistics(symbol)
daily_change_percent = get_24hr_price_change_percent(symbol) 

print(daily_change_percent)


