from common import get_average_ratio

"""Simple moving average (SMA) algorithm"""
long_term = 56
short_term = 14

BASE_CURRENCY = 'USD'
TARGET_CURRENCY = 'BTC'


short_term_average = get_average_ratio(short_term, BASE_CURRENCY, TARGET_CURRENCY)
long_term_average = get_average_ratio(long_term, BASE_CURRENCY, TARGET_CURRENCY)

print(f'{short_term} days average {TARGET_CURRENCY}/{BASE_CURRENCY} ratio: {short_term_average:.4f}')
print(f'{long_term} days average {TARGET_CURRENCY}/{BASE_CURRENCY} ratio: {long_term_average:.4f}')
print(f'The diff is: {(abs(short_term_average-long_term_average))}')
# Whenever the short term average goes over long term average, we sould buy
if short_term_average > long_term_average:
    print(f'You should BUY {TARGET_CURRENCY} now, beacuse the short term average is above long term average')
else:
    print(f'You should SELL {TARGET_CURRENCY} now, beacuse the short term average is below long term average')