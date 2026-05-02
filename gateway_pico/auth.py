try:
    import uhashlib as hashlib
except ImportError:
    import hashlib

import config


SESSION_COOKIE = "gateway_session"


def sha256_hex(value):
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return "".join("%02x" % byte for byte in digest)


def credentials_are_valid(username, password):
    return (
        username == config.ADMIN_USERNAME
        and sha256_hex(password) == config.ADMIN_PASSWORD_SHA256
    )


def session_cookie_header():
    return "%s=%s; Path=/; HttpOnly; SameSite=Strict" % (
        SESSION_COOKIE,
        config.ADMIN_SESSION_TOKEN,
    )


def logout_cookie_header():
    return "%s=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict" % SESSION_COOKIE


def is_authenticated(headers):
    cookie_header = headers.get("cookie", "")
    expected = "%s=%s" % (SESSION_COOKIE, config.ADMIN_SESSION_TOKEN)

    for cookie in cookie_header.split(";"):
        if cookie.strip() == expected:
            return True

    return False
