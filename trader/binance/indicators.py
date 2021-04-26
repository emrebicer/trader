import trader.binance.helper
import trader.indicators

def get_close_data(symbol, interval, data_count) -> list:
    """
        Returns a list of floats
    """
    klines = trader.binance.helper.get_klines_data(symbol, interval, data_count + 1)
    
    close_data = []
    for data_point in klines:
        close_data.append(float(data_point[4]))
    
    return close_data

def get_rsi(symbol, interval, moving_average = 0, data_count = 14) -> float:
    """
        Returns Relative Strength Index

        moving_average
            0 - SMA (Simple Moving Average)
            1 - EMA (Exponential Moving Average)
    """

    # Fetch <data_count + 1> days to calculate the change on <data_count> days
    close_data = get_close_data(symbol, interval, data_count + 1)
    return trader.indicators.get_rsi(close_data, moving_average)


def get_bollinger_bands(symbol, interval, data_count = 20) -> (float, float, float):
    """
        Returns (upper, middle, lower) bollinger bands
    """

    close_data = get_close_data(symbol, interval, data_count)
    return trader.indicators.get_bollinger_bands(close_data)

def get_sma(symbol, interval, data_count = 9) -> float:
    """
        Returns simple moving average
    """

    close_data = get_close_data(symbol, interval, data_count)
    return trader.indicators.get_sma(close_data)

def get_ema(symbol, interval, data_count = 9) -> float:
    """
        Returns exponential moving average
    """
    
    close_data = get_close_data(symbol, interval, data_count)
    return trader.indicators.get_ema(close_data)
