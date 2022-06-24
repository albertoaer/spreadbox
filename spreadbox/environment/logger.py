class Logger:
    def __init__(self, context : str) -> None:
        self.context = context

    def log(self, header, msg):
        print("%s [%s]: %s" % (header, self.context, msg))

    def info(self, msg) -> None: self.log("INFO", msg)
    def warn(self, msg) -> None: self.log("WARN", msg)
    def err(self, msg) -> None: self.log("ERROR", msg)