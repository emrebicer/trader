import requests
import sys
sys.path.append("../")
# pylint: disable=import-error
import trader.indicators 
import trader.binance.indicators

BASE_ENDPOINT = 'https://api.binance.com/api/v3/'
POSITIVE_EMOJI = "✅"    
NEGATIVE_EMOJI = "⛔"

money = 100
buy_next = True
lop = -1
glob_max_found = -1
glob_max_found_str = ''

def perform_bot_operations(klines, rsi_data_count, bollinger_data_count, bsl, ssl, avoid_loss):
    global money
    global buy_next 
    global lop

    if len(klines) == 0:
        return

    current_price = float(klines[-1])
    buy_signal = 0
    sell_signal = 0

    # RSI indicator
    rsi_margin = 4.0
    rsi = trader.indicators.get_rsi(klines[len(klines) - rsi_data_count:])
    if rsi >= 70 - rsi_margin:
        sell_signal += 1
    elif rsi <= 30 + rsi_margin:
        buy_signal += 1

    # Bollinger bands indicator
    (upper, _, lower) = trader.indicators.get_bollinger_bands(klines[len(klines) - bollinger_data_count:])
    if current_price > upper:
        sell_signal += 1
    elif current_price < lower:
        buy_signal += 1

    # Simple moving average
    sma = trader.indicators.get_sma(klines)
    if current_price > sma:
        sell_signal += 1
    elif current_price < sma:
        buy_signal += 1

    # Exponential moving average (4h)
    ema = trader.indicators.get_ema(klines)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1

    # Exponential moving average (1d)
    ema = trader.indicators.get_ema(klines)
    if current_price > ema:
        sell_signal += 1
    elif current_price < ema:
        buy_signal += 1
    
    if buy_signal >= bsl:
        if buy_next:
            # Buy
            #print(f'Bought at {current_price} with {money} USDT')
            money = money / current_price
            buy_next = not buy_next
            lop = current_price
    elif sell_signal >= ssl:
        if not buy_next:
            if not avoid_loss or (avoid_loss and lop < current_price):
                # Sell
                money = money * current_price
                buy_next = not buy_next
                lop = current_price
                #print(f'Sold at {current_price} for {money} USDT')


def simulate(symbol, interval, limit, rsi_data_count = 14, bollinger_data_count = 20):
    close_data = trader.binance.indicators.get_close_data(symbol, interval, limit)
    data_period = max(rsi_data_count, bollinger_data_count)

    buy_signal_limits = [2,3,4,5]
    sell_signal_limits = [2,3,4,5]
    avoid_loss = [True, False]

    global money
    global buy_next

    max_found = -1
    max_found_str = ''

    for bsl in buy_signal_limits:
        for ssl in sell_signal_limits:
            for al in avoid_loss:
                money = 100
                buy_next = True
                for i in range(data_period, len(close_data) - data_period):
                    current_data = close_data[i - data_period: i]
                    try:
                        perform_bot_operations(current_data, rsi_data_count, bollinger_data_count, bsl, ssl, al)
                    except:
                        print(f'ERR ON: bsl:{bsl} - ssl:{ssl} - avoid_loss:{al} - interval:{interval}')

                if not buy_next:
                    money *= close_data[-1]
                
                st = f'bsl:{bsl} - ssl:{ssl} - avoid_loss:{al} - interval:{interval} / money:{money}'
                if money > max_found:
                    max_found = money
                    max_found_str = st
                # uncomment this to see all possible outputs
                #print(st)

    print(f'MAX FOUND: {max_found_str}')

    global glob_max_found
    global glob_max_found_str

    if max_found > glob_max_found:
        glob_max_found = max_found
        glob_max_found_str = max_found_str
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Please provide 1 argument; SYMBOL")
        exit()
    """
        NOTE: looking at different intervals is not a good idea
        since we are always capturing same amount of kline data,
        the actual time-frame is changing according to the interval.
        Since the difference is growing as you go back in time,
        the longer intervals should always result in more profit... 
    """

    #intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]

    max_possible = 999
    intervals = {
        "30m": max_possible,
        "1h": max_possible / 2,
        "2h": max_possible / 4,
        "4h": max_possible / 8,
    }
    for interval in intervals:
        #simulate(sys.argv[1], interval, 999)
        simulate(sys.argv[1], interval, intervals[interval])
    

    print(f'\nBest:\n\n{glob_max_found_str}')

