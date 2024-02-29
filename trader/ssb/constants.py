LOG_FILE = 'log_signal_spot_bot.txt'
ERROR_LOG_FILE = 'error_log_signal_spot_bot.txt'
CONFIG_FILE = 'config_signal_spot_bot.json'
EXPECTED_CONFIG_KEYS = {
    'enabled': bool,
    'base_currency': str,
    'target_currency': str,
    'buy_on_next_trade': bool,
    'trade_amount_buy': float,
    'trade_wealth_percent_sell': float,
    'last_operation_price': float,
    'prevent_loss': bool,
    'hook_percent': float,
}
