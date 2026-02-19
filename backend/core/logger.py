import logging
import sys
import os

# custom success level (between info and warning)
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kws):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)

logging.Logger.success = success

class LowercaseColorFormatter(logging.Formatter):
    """
    custom formatter providing ansi colors in a clean, lowercase, emoji-free format.
    automatically detects aws lambda and strips colors to keep cloudwatch clean.
    """
    
    # ansi escape codes
    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    format_str = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # detect lambda environment
        self.is_lambda = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    def get_formats(self):
        # if in lambda, return plain formats (no ansi)
        if self.is_lambda:
            return {level: self.format_str for level in [
                logging.DEBUG, logging.INFO, SUCCESS_LEVEL_NUM, 
                logging.WARNING, logging.ERROR, logging.CRITICAL
            ]}
            
        return {
            logging.DEBUG: self.GREY + self.format_str + self.RESET,
            logging.INFO: self.BLUE + self.format_str + self.RESET,
            SUCCESS_LEVEL_NUM: self.GREEN + self.format_str + self.RESET,
            logging.WARNING: self.YELLOW + self.format_str + self.RESET,
            logging.ERROR: self.RED + self.format_str + self.RESET,
            logging.CRITICAL: self.BOLD_RED + self.format_str + self.RESET
        }

    def format(self, record):
        # convert level name to lowercase for output
        record.levelname = record.levelname.lower()
        
        # apply color based on original levelno
        formats = self.get_formats()
        log_fmt = formats.get(record.levelno, self.format_str)
        
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        
        # force result string to be lowercase
        formatted = formatter.format(record)
        return formatted.lower()

def setup_logger():
    """
    configures the root logger to use the ansi lowercase formatter.
    call this once at application startup.
    """
    root_logger = logging.getLogger()
    
    # clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(LowercaseColorFormatter())
    
    root_logger.addHandler(console_handler)
    
    # quiet down noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
