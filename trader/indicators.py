"""
    Indicator functions

    NOTE: if more indicator functions will be implemented using other 
    platforms than binance, this script should be refactored 
    and another indicator.py file should be added to 
    binance folder and other desired platform folders
    
    in that case, the functions in this file should only
    accept klines data (and other independent parameters),
    not symbol, interval etc.
"""
import trader.binance.helper


def get_rsi(symbol, interval, moving_average = 0, data_count = 14) -> float:
    """
        Returns Relative Strength Index

        moving_average
            0 - SMA (Simple Moving Average)
            1 - EMA (Exponential Moving Average)
    """

    # Fetch <data_count + 1> days to calculate the change on <data_count> days
    klines = trader.binance.helper.get_klines_data(symbol, interval, data_count + 1)

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

def get_bollinger_bands(symbol, interval, data_count = 20) -> (float, float, float):
    """
        Returns (upper, middle, lower) bollinger bands
    """

    klines = trader.binance.helper.get_klines_data(symbol, interval, data_count)

    closes = []

    for kline in klines:
        closes.append(float(kline[4]))

    close_average = sum(closes) / len(closes)

    squared_total = 0.0
    for close in closes:
        diff = close_average - close
        squared_total += diff * diff

    average_squared_total = squared_total / len(closes) 
    deviation = average_squared_total ** (1 / 2)

    upper_bollinger_band = close_average + (2 * deviation)
    middle_bollinger_band = close_average
    lower_bollinger_band = close_average - (2 * deviation)

    return (upper_bollinger_band, middle_bollinger_band, lower_bollinger_band)

def get_sma(symbol, interval, data_count = 9) -> float:
    """
        Returns simple moving average
    """
    klines = trader.binance.helper.get_klines_data(symbol, interval, data_count)
    closes = []

    for kline in klines:
        closes.append(float(kline[4]))
    
    return sum(closes) / len(closes)

def get_ema(symbol, interval, data_count = 9) -> float:
    """
        Returns exponential moving average
    """
    klines = trader.binance.helper.get_klines_data(symbol, interval, data_count)
    closes = []

    for kline in klines:
        closes.append(float(kline[4]))
    
    # First EMA is calculated as simple moving average of given close points
    ema = get_sma(symbol, interval, data_count * 4)
    a = 2 / ( len(closes) + 1 )

    for index in range(1, len(closes)):
        ema = a * closes[index] + (1 - a) * ema

    return ema
