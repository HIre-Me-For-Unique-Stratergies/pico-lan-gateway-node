try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

try:
    import ubinascii as binascii
except ImportError:
    import binascii

try:
    import uos as os
except ImportError:
    import os

try:
    import machine
except ImportError:
    machine = None

import time

import config


SESSION_COOKIE = "gateway_session"
CLIENT_TOKEN_COOKIE = "gateway_client_token"
CSRF_COOKIE = "gateway_csrf"
SETTINGS_FILE = "settings.py"
_current_session_token = ""
_current_session_hash = ""
_current_client_token = ""
_current_client_hash = ""
_session_expires_at = 0
_backend_token = ""
_backend_token_hash = ""
_csrf_token = ""
_csrf_hash = ""

try:
    import settings
except ImportError:
    settings = None


def sha256_hex(value):
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return "".join("%02x" % byte for byte in digest)


def digest_hex(digest):
    return "".join("%02x" % byte for byte in digest)


def hash_password(password, salt, rounds=None):
    if rounds is None:
        rounds = getattr(config, "PASSWORD_HASH_ROUNDS", 1000)

    value = ("%s:%s" % (salt, password)).encode("utf-8")

    for _ in range(rounds):
        value = hashlib.sha256(value).digest()

    return digest_hex(value)


def token_hash(value):
    return sha256_hex(value)


def _ticks_value():
    if hasattr(time, "ticks_us"):
        return time.ticks_us()
    return int(time.time() * 1000000)


def _fallback_random_nibble():
    value = _ticks_value()

    if machine is not None and hasattr(machine, "rng"):
        try:
            value ^= machine.rng()
        except Exception:
            pass

    return value & 0x0f


def token_hex(length=32):
    try:
        random_bytes = os.urandom((length + 1) // 2)
        return binascii.hexlify(random_bytes).decode("ascii")[:length]
    except Exception:
        pass

    chars = "0123456789abcdef"
    value = ""

    for _ in range(length):
        value += chars[_fallback_random_nibble()]

    return value


def _string_literal(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _token_is_safe(value):
    if not value:
        return False

    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
    for char in value:
        if char not in allowed:
            return False

    return len(value) >= 24


def _set_runtime_settings(username, password_salt, password_hash_value, password_hash_rounds):
    global settings

    class RuntimeSettings:
        pass

    runtime_settings = RuntimeSettings()
    runtime_settings.ADMIN_USERNAME = username
    runtime_settings.ADMIN_PASSWORD_SALT = password_salt
    runtime_settings.ADMIN_PASSWORD_HASH = password_hash_value
    runtime_settings.PASSWORD_HASH_ROUNDS = password_hash_rounds
    settings = runtime_settings


def _now():
    return time.time()


def _session_timeout_seconds():
    return getattr(config, "SESSION_TIMEOUT_SECONDS", 900)


def _session_is_active():
    return bool(_current_session_hash) and _now() < _session_expires_at


def _set_backend_token(value=""):
    global _backend_token, _backend_token_hash

    if not _token_is_safe(value):
        value = token_hex(48)

    _backend_token = value
    _backend_token_hash = token_hash(value)


def ensure_csrf_token():
    global _csrf_token, _csrf_hash

    if not _csrf_token:
        _csrf_token = token_hex(48)
        _csrf_hash = token_hash(_csrf_token)

    return _csrf_token


def csrf_cookie_header():
    return "%s=%s; Path=/; Max-Age=%s; HttpOnly; SameSite=Strict" % (
        CSRF_COOKIE,
        ensure_csrf_token(),
        _session_timeout_seconds(),
    )


def logout_csrf_cookie_header():
    return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict" % CSRF_COOKIE


def csrf_token_is_valid(headers, form):
    expected_form_token = form.get("csrf_token", "")
    cookie_token = _cookie_value(headers, CSRF_COOKIE)

    if not expected_form_token or not cookie_token or not _csrf_hash:
        return False

    if token_hash(expected_form_token) != _csrf_hash:
        return False

    return token_hash(cookie_token) == _csrf_hash


def begin_session(client_token_value=""):
    global _current_session_token
    global _current_session_hash
    global _current_client_token
    global _current_client_hash
    global _session_expires_at

    if not _token_is_safe(client_token_value):
        client_token_value = token_hex(48)

    _current_session_token = token_hex(48)
    _current_session_hash = token_hash(_current_session_token)
    _current_client_token = client_token_value
    _current_client_hash = token_hash(_current_client_token)
    _session_expires_at = _now() + _session_timeout_seconds()


def refresh_session():
    global _session_expires_at

    if _session_is_active():
        _session_expires_at = _now() + _session_timeout_seconds()


def clear_session():
    global _current_session_token
    global _current_session_hash
    global _current_client_token
    global _current_client_hash
    global _session_expires_at
    global _csrf_token
    global _csrf_hash

    _current_session_token = ""
    _current_session_hash = ""
    _current_client_token = ""
    _current_client_hash = ""
    _session_expires_at = 0
    _csrf_token = ""
    _csrf_hash = ""


def session_seconds_remaining():
    remaining = int(_session_expires_at - _now())
    if remaining < 0:
        return 0
    return remaining


def is_configured():
    if settings is None:
        return False

    return bool(
        getattr(settings, "ADMIN_PASSWORD_HASH", "")
        or getattr(settings, "ADMIN_PASSWORD_SHA256", "")
    )


def configured_username():
    if settings is None:
        return config.DEFAULT_ADMIN_USERNAME
    return getattr(settings, "ADMIN_USERNAME", config.DEFAULT_ADMIN_USERNAME)


def configured_password_hash():
    if settings is None:
        return ""
    return getattr(
        settings,
        "ADMIN_PASSWORD_HASH",
        getattr(settings, "ADMIN_PASSWORD_SHA256", ""),
    )


def configured_password_salt():
    if settings is None:
        return ""
    return getattr(settings, "ADMIN_PASSWORD_SALT", "")


def configured_password_rounds():
    if settings is None:
        return getattr(config, "PASSWORD_HASH_ROUNDS", 1000)
    return getattr(settings, "PASSWORD_HASH_ROUNDS", getattr(config, "PASSWORD_HASH_ROUNDS", 1000))


def backend_token():
    if not _backend_token:
        _set_backend_token()
    return _backend_token


def backend_token_is_valid(value):
    if not _backend_token_hash:
        _set_backend_token()
    return bool(value) and token_hash(value) == _backend_token_hash


def save_first_run_setup(username, password, client_token_value="", backend_token_value=""):
    if not username:
        username = config.DEFAULT_ADMIN_USERNAME

    if not password or len(password) < config.MIN_ADMIN_PASSWORD_LENGTH:
        return False

    password_salt = token_hex(32)
    password_hash_value = hash_password(password, password_salt)
    password_hash_rounds = getattr(config, "PASSWORD_HASH_ROUNDS", 1000)

    if not _token_is_safe(client_token_value):
        client_token_value = token_hex(48)

    if not _token_is_safe(backend_token_value):
        backend_token_value = token_hex(48)

    content = (
        'ADMIN_USERNAME = "%s"\n'
        'ADMIN_PASSWORD_SALT = "%s"\n'
        'ADMIN_PASSWORD_HASH = "%s"\n'
        'PASSWORD_HASH_ROUNDS = %s\n'
    ) % (
        _string_literal(username),
        _string_literal(password_salt),
        password_hash_value,
        password_hash_rounds,
    )

    with open(SETTINGS_FILE, "w") as handle:
        handle.write(content)

    _set_runtime_settings(
        username,
        password_salt,
        password_hash_value,
        password_hash_rounds,
    )
    _set_backend_token(backend_token_value)
    begin_session(client_token_value)

    return True


def credentials_are_valid(username, password):
    if not is_configured() or username != configured_username():
        return False

    password_salt = configured_password_salt()

    if password_salt:
        return hash_password(password, password_salt, configured_password_rounds()) == configured_password_hash()

    return sha256_hex(password) == configured_password_hash()


def session_cookie_header():
    return "%s=%s; Path=/; HttpOnly; SameSite=Strict" % (
        SESSION_COOKIE,
        _current_session_token,
    )


def client_token_cookie_header():
    return "%s=%s; Path=/; HttpOnly; SameSite=Strict" % (
        CLIENT_TOKEN_COOKIE,
        _current_client_token,
    )


def logout_cookie_header():
    return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict" % SESSION_COOKIE


def logout_client_token_cookie_header():
    return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict" % CLIENT_TOKEN_COOKIE


def _cookie_value(headers, name):
    cookie_header = headers.get("cookie", "")
    prefix = "%s=" % name

    for cookie in cookie_header.split(";"):
        clean_cookie = cookie.strip()
        if clean_cookie.startswith(prefix):
            return clean_cookie[len(prefix):]

    return ""


def _cookie_hash_matches(headers, name, expected_hash):
    if not expected_hash:
        return False

    value = _cookie_value(headers, name)
    if not value:
        return False

    return token_hash(value) == expected_hash


def is_authenticated(headers):
    if not _session_is_active():
        clear_session()
        return False

    return _cookie_hash_matches(headers, SESSION_COOKIE, _current_session_hash)


def client_token_is_valid(headers):
    header_token = headers.get("x-client-token", "")

    if not _session_is_active():
        clear_session()
        return False

    if header_token and token_hash(header_token) == _current_client_hash:
        return True

    return _cookie_hash_matches(headers, CLIENT_TOKEN_COOKIE, _current_client_hash)


_set_backend_token()
