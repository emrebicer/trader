import requests
import sys

BASE_ENDPOINT = 'https://api.binance.com/api/v3/'
POSITIVE_EMOJI = "✅"    
NEGATIVE_EMOJI = "⛔"



def get_klines_data(symbol, interval, limit = 1000):
    accepted_intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"]
    
    if interval not in accepted_intervals:
        raise Exception(f'{interval} is not accepted; must be {accepted_intervals}')


    api_endpoints = BASE_ENDPOINT + f'klines?symbol={symbol}&interval={interval}&limit={limit}'

    response = requests.get(api_endpoints)

    if response.status_code != 200:
        raise Exception(f'Failed while fetching klines data, response: {response}')
    
    return response.json()


res = get_klines_data("BTCUSDT", "1d")


def get_statistics(symbol, interval, limit = 1000):
    
    klines_data = get_klines_data(symbol, interval, limit)
    
    previous_data = klines_data[0]
    
    closed_higher_count = 0
    closed_lower_count = 0
    increase_average = 0
    decrease_average = 0
    max_increase = 0
    max_decrease = 0
    all_close_average = 0


    for current_kline in klines_data:

        for data_index in range(len(current_kline)):
            current_kline[data_index] = float(current_kline[data_index])
        
        all_close_average += current_kline[4]

        if previous_data[0] == current_kline[0]:
            continue
        
        if current_kline[4] > previous_data[4]:
            closed_higher_count += 1
            increase_average += current_kline[4] - previous_data[4]
            if current_kline[4] - previous_data[4] > max_increase:
                max_increase = current_kline[4] - previous_data[4]
            print(POSITIVE_EMOJI, end = '')
        else:
            closed_lower_count += 1
            decrease_average += current_kline[4] - previous_data[4]
            if current_kline[4] - previous_data[4] < max_decrease:
                max_decrease = current_kline[4] - previous_data[4]

            print(NEGATIVE_EMOJI, end = '')
        previous_data = current_kline
    
    
    increase_average = increase_average / closed_higher_count
    decrease_average = decrease_average / closed_lower_count
    all_close_average = all_close_average / (len(klines_data) - 1)

    print('\n\n\n')
    print(f'Closed higher: {closed_higher_count} --- ({closed_higher_count * 100.0 / (len(klines_data) - 1)}%) {POSITIVE_EMOJI}')
    print(f'Closed lower : {closed_lower_count} --- ({closed_lower_count * 100.0 / (len(klines_data) - 1)}%) {NEGATIVE_EMOJI}')
    print(f'Increase average: {increase_average}')
    print(f'Decrease average: {decrease_average}')
    print(f'Max increase: {max_increase}')
    print(f'Max decrease: {max_decrease}')
    print(f'All close average: {all_close_average}')


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Please provide 3 arguments; SYMBOL, INTERVAL and LIMIT")
        exit()
    get_statistics(sys.argv[1], sys.argv[2], sys.argv[3])

