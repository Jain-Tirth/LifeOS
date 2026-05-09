import logging
import json
import re
from datetime import datetime

class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from log messages"""
    SENSITIVE_PATTERNS = [
        (r'password["\']?\s*[:=]\s*["\']?[^"\',\s]+', 'password=[REDACTED]'),
        (r'Authorization:\s*Bearer\s+\S+', 'Authorization: Bearer [REDACTED]'),
        (r'api_key["\']?\s*[:=]\s*["\']?[^"\',\s]+', 'api_key=[REDACTED]'),
        (r'token["\']?\s*[:=]\s*["\']?[^"\',\s]+', 'token=[REDACTED]'),
        (r'secret["\']?\s*[:=]\s*["\']?[^"\',\s]+', 'secret=[REDACTED]'),
        (r'email["\']?\s*[:=]\s*["\']?[^"\',\s@]+@[^"\',\s]+', 'email=[REDACTED]'),
    ]
    
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg)
        elif isinstance(record.msg, dict):
            # Redact sensitive keys in dict messages
            sensitive_keys = ['password', 'token', 'api_key', 'secret', 'authorization']
            for key in sensitive_keys:
                if key in record.msg:
                    record.msg[key] = '[REDACTED]'
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        from lifeos.middleware import correlation_id_var
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_obj['correlation_id'] = correlation_id

        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_obj)
