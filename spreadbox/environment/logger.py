import logging
import ctypes
import sys

class Formatter(logging.Formatter):
    grey = "\x1b[38m"
    blue = "\x1b[34m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    template='%(asctime)s [ %(name)s ] %(message)s'
    
    formats = { logging.DEBUG: grey, logging.INFO: blue, logging.WARNING: yellow,
                logging.ERROR: bold_red, logging.CRITICAL: red }

    def format(self, record):
        return logging.Formatter(self.formats[record.levelno] + self.template + self.reset).format(record)

def setup():
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(Formatter())
    logging.basicConfig(
        level=logging.NOTSET,
        handlers=[
            stream
        ]
    )
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)