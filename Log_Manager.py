import logging

class Log:
    def __init__(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def set_logger(self):
        if not self.logger.handlers:
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(self.formatter)
            self.logger.addHandler(stream_handler)
            file_handler = logging.FileHandler('server.log')
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)

    def logging(self, msg):
        self.set_logger()
        self.logger.info(msg)