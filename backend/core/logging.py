import logging
import sys
import json
import contextvars
from datetime import datetime, timezone

# Context var for request-scoped correlation ID
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
            "request_id": request_id_var.get("-"),
        }

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def configure_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root.handlers = []
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").disabled = True
