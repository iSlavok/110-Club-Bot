import hashlib
import hmac
import secrets
from collections.abc import Mapping

LOGIN_CODE_DIGITS = 6


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def generate_login_code() -> str:
    return f"{secrets.randbelow(10**LOGIN_CODE_DIGITS):0{LOGIN_CODE_DIGITS}d}"


# https://core.telegram.org/widgets/login#checking-authorization
def is_valid_widget_signature(fields: Mapping[str, object], signature: str, bot_token: str) -> bool:
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
