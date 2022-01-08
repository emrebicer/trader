from typing import Tuple

def get_rsi(data_points, moving_average = 0) -> float:
    """
        Returns Relative Strength Index

        moving_average
            0 - SMA (Simple Moving Average)
            1 - EMA (Exponential Moving Average)
    """

    change_up = []
    change_down = []

    if len(data_points) == 0:
        return 0

    for index in range(1, len(data_points)):

        current_close = data_points[index]
        prev_close = data_points[index - 1]

        diff = current_close - prev_close

        if diff > 0:
            change_up.append(diff)
            change_down.append(0)
        else:
            change_down.append(-diff)
            change_up.append(0)
    
    if len(change_up) == 0:
        return 0
    elif len(change_down) == 0:
        return 100

    up_avg = sum(change_up) / len(change_up)
    down_avg = sum(change_down) / len(change_down)

    if moving_average == 0:
        rs = up_avg / down_avg 
        return 100 - (100 / (1 + rs))

    elif moving_average == 1:
        a = 2 / ( len(data_points) + 1 )
        for index in range(0, len(change_up)):
            up_avg = a * change_up[index] + (1 - a) * up_avg 

        for index in range(0, len(change_down)):
            down_avg = a * change_down[index] + (1 - a) * down_avg 

        rs = up_avg / down_avg 
        rsi = 100 - (100 / ( 1 + rs))
        return rsi

    else:
        raise Exception(f'<{moving_average}> is not valid for moving average parameter')

def get_bollinger_bands(data_points) -> Tuple[float, float, float]:
    """
        Returns (upper, middle, lower) bollinger bands
    """

    close_average = sum(data_points) / len(data_points)

    squared_total = 0.0
    for data_point in data_points:
        diff = close_average - data_point 
        squared_total += diff * diff

    average_squared_total = squared_total / len(data_points) 
    deviation = average_squared_total ** (1 / 2)

    upper_bollinger_band = close_average + (2 * deviation)
    middle_bollinger_band = close_average
    lower_bollinger_band = close_average - (2 * deviation)

    return (upper_bollinger_band, middle_bollinger_band, lower_bollinger_band)

def get_sma(data_points) -> float:
    """
        Returns simple moving average
    """
    
    return sum(data_points) / len(data_points)

def get_ema(data_points) -> float:
    """
        Returns exponential moving average
    """
    
    # First EMA is calculated as simple moving average of given close points
    ema = get_sma(data_points)
    a = 2 / ( len(data_points) + 1 )

    for index in range(1, len(data_points)):
        ema = a * data_points[index] + (1 - a) * ema

    return ema
