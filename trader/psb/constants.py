LOG_FILE = 'log_primitive_spot_bot.txt'
ERROR_LOG_FILE = 'error_log_primitive_spot_bot.txt'
CONFIG_FILE = 'config_primitive_spot_bot.json'
EXPECTED_CONFIG_KEYS = {
    'enabled': bool,
    'base_currency': str,
    'target_currency': str,
    'buy_on_next_trade': bool,
    'last_operation_price': float,
    'profit_percent_buy': float,
    'profit_percent_sell': float,
    'hook_percent': float,
    'trade_with_percent_buy': bool,
    'trade_amount_buy': float,
    'trade_wealth_percent_buy': float,
    'trade_wealth_percent_sell': float,
    'loss_prevention': bool,
    'loss_prevention_percent': float,
    'avoid_buy_on_daily_increase': bool,
    'avoid_buy_on_daily_increase_percent': float,
    'avoid_buy_on_average_increase': bool,
    'avoid_buy_on_average_day_count': int,
    'last_trade_time_stamp': float,
    'update_lop_on_idle': bool, 
    'update_lop_on_idle_days': int 
}