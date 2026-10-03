import logging
import sys

from utils import mask_sensitive_data


class MaskSensitiveFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str):
                record.msg = mask_sensitive_data(record.msg)
            if record.args:
                new_args = []
                for arg in record.args:
                    if isinstance(arg, str):
                        new_args.append(mask_sensitive_data(arg))
                    else:
                        new_args.append(arg)
                record.args = tuple(new_args)
        except Exception:
            pass
        return True


def setup_logger(name: str = "netflix_relay", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(level)
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(MaskSensitiveFilter())

    logger.addFilter(MaskSensitiveFilter())
    logger.addHandler(handler)
    return logger
