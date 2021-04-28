import trader.psb.constants
import trader.helper 

def load_config_file(default_config) -> list:
    return trader.helper.load_config_file(trader.psb.constants.CONFIG_FILE, default_config)

def write_config_file(config):
    trader.helper.write_config_file(trader.psb.constants.CONFIG_FILE, config)

def validate_config_file(config):
    trader.helper.validate_config_file(config, trader.psb.constants.EXPECTED_CONFIG_KEYS)

def log(message, dump_to_console):
    trader.helper.log(trader.psb.constants.LOG_FILE, message, dump_to_console)

def error_log(message, dump_to_console):
    trader.helper.error_log(trader.psb.constants.ERROR_LOG_FILE, message, dump_to_console)
