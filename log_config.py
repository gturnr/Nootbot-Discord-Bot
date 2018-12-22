import logging

formatter = logging.Formatter('%(asctime)s [%(levelname)s] | %(message)s')

def setup_logger(name, log_file, level=logging.INFO, console_level=logging.WARNING):
    handler = logging.FileHandler(log_file, encoding='utf-8', mode='a')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(console_level)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger
