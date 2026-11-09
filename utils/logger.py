"""Logging for JARVIS: a normal app log and a separate audit log of every action."""
import logging
import os

import config

os.makedirs(config.LOGS_DIR, exist_ok=True)


def _make_logger(name: str, filename: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # already set up, do not add a second handler
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(os.path.join(config.LOGS_DIR, filename), encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False
    return logger


app_log = _make_logger("jarvis.app", "jarvis.log")
audit_log = _make_logger("jarvis.audit", "audit.log")


def audit(tool: str, args: dict, status: str, result: str = "") -> None:
    """Write one line to logs/audit.log for every action JARVIS tries."""
    short = str(result).replace("\n", " ")[:200]
    audit_log.info("tool=%s | args=%s | status=%s | result=%s", tool, args, status, short)
