import json
import logging
import sys


class JSONFormatter(logging.Formatter):
    """A JSON formatter that converts the standard log record fields into a JSON string."""

    def format(self, record):
        record_dict = {
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "pathname": record.pathname,
            "lineno": record.lineno,
            "time": self.formatTime(record, self.datefmt),
        }
        return json.dumps(record_dict)


def setup_logger(level: str = logging.DEBUG) -> logging.Logger:
    """Configures the root logger with jsonFormatter and specified log level."""

    log = logging.getLogger()
    if not log.handlers:

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())

        log.addHandler(handler)
        log.setLevel(level)

    return log
