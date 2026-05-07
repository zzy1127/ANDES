"""Project-wide logger with an extra ``SUCCESS`` level."""

import logging

SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


def _success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)


# Attach `success(...)` to every Logger instance project-wide.
logging.Logger.success = _success


def get_logger(name: str = "andes") -> logging.Logger:
    """Return a configured logger for the ``andes.*`` namespace.

    A single ``StreamHandler`` is attached on first use so that nested
    invocations (e.g. multiple operators in one process) do not duplicate log
    lines.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
