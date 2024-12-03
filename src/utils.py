import yaml
import sys
from loguru import logger

def load_config(config_path: str) -> dict:
    """
    Loads the configuration from a YAML file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Loaded configuration data.
    """
    try:
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        raise



def setup_logger(log_file: str = "app.log", level: str = "INFO"):
    """
    Sets up the logger for the application. This logger can log to the console and to a file.
    
    Args:
        name (str): The name of the logger, defaults to None, which will use 'app'.
        log_file (str): The file where logs should be written, defaults to 'app.log'.
        level (str): The log level for the logger (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
    """
    # Set up logging to file
    logger.remove()  # Remove default logger
    logger.add(sys.stdout, level=level)  # Log to stdout (console)
    logger.add(log_file, level=level, rotation="1 week", compression="zip")  # Log to file with rotation
    
    return logger  


