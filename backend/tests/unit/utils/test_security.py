import hashlib
import hmac

from app.utils import generate_login_code, hash_secret, is_valid_widget_signature

TOKEN = "123456:test-token"


def _sign(fields: dict[str, object]) -> str:
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hashlib.sha256(TOKEN.encode()).digest()
    return hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()


def test_login_code_is_six_digits() -> None:
    codes = {generate_login_code() for _ in range(50)}

    assert all(len(code) == 6 and code.isdigit() for code in codes)


def test_hash_is_stable_and_hides_value() -> None:
    assert hash_secret("123456") == hash_secret("123456")
    assert "123456" not in hash_secret("123456")


def test_widget_signature_accepts_telegram_signed_data() -> None:
    fields = {"id": 42, "first_name": "Ann", "auth_date": 1_700_000_000}

    assert is_valid_widget_signature(fields, _sign(fields), TOKEN)


def test_widget_signature_rejects_tampered_data() -> None:
    fields = {"id": 42, "first_name": "Ann", "auth_date": 1_700_000_000}
    signature = _sign(fields)

    assert not is_valid_widget_signature({**fields, "id": 43}, signature, TOKEN)


def test_widget_signature_rejects_non_ascii_instead_of_crashing() -> None:
    fields = {"id": 42, "first_name": "Ann", "auth_date": 1_700_000_000}

    assert not is_valid_widget_signature(fields, "я" * 64, TOKEN)
