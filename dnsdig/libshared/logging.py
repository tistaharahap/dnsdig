import logging
import sys
from uuid import uuid4

request_id = ''


def set_request_id(new_request_id):
    global request_id
    request_id = new_request_id if new_request_id else uuid4()


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id
        return True


class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


logging.root.setLevel(logging.INFO)
logger = logging.getLogger('fastapi')
logger.propagate = False

# handlers, filter, format
formatter = logging.Formatter('%(asctime)-15s %(request_id)s [%(levelname)s] %(message)s')
h_err = logging.StreamHandler(sys.stderr)
h_err.addFilter(RequestIdFilter())
h_err.setLevel(logging.WARNING)
h_err.setFormatter(formatter)

h_out = logging.StreamHandler(sys.stdout)
h_out.addFilter(RequestIdFilter())
h_out.addFilter(MaxLevelFilter(logging.WARNING))
h_out.setLevel(logging.INFO)
h_out.setFormatter(formatter)

logger.addHandler(h_err)
logger.addHandler(h_out)
