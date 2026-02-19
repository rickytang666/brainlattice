import logging
import sys

class LowercaseColorFormatter(logging.Formatter):
    """
    custom formatter providing ansi colors in a clean, lowercase, emoji-free format.
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

    FORMATS = {
        logging.DEBUG: GREY + format_str + RESET,
        logging.INFO: BLUE + format_str + RESET,
        logging.WARNING: YELLOW + format_str + RESET,
        logging.ERROR: RED + format_str + RESET,
        logging.CRITICAL: BOLD_RED + format_str + RESET
    }

    def format(self, record):
        # convert level name to lowercase for output
        record.levelname = record.levelname.lower()
        
        # apply color based on original levelno
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.DEBUG])
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
