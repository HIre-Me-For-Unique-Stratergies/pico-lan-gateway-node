import time
try:
    import gc
except ImportError:
    gc = None

import auth
import config


START_TIME = time.time()


def ticks_ms():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def ticks_diff(end, start):
    if hasattr(time, "ticks_diff"):
        return time.ticks_diff(end, start)
    return end - start


def status_body(ip_address):
    uptime_seconds = int(time.time() - START_TIME)
    return (
        '{"service":"lan-gateway-node",'
        '"device":"%s",'
        '"mode":"%s",'
        '"ip_address":"%s",'
        '"status":"ready",'
        '"uptime_seconds":%s}\n'
    ) % (config.DEVICE_NAME, config.MODE, ip_address, uptime_seconds)


def api_body():
    return '{"message":"Hello from the single Pico LAN Gateway Node"}\n'


def diagnostics_body(ip_address):
    free_memory = -1

    if gc is not None and hasattr(gc, "mem_free"):
        try:
            free_memory = gc.mem_free()
        except Exception:
            free_memory = -1

    uptime_seconds = int(time.time() - START_TIME)
    return (
        '{"device":"%s",'
        '"mode":"%s",'
        '"ip_address":"%s",'
        '"uptime_seconds":%s,'
        '"free_memory_bytes":%s,'
        '"discovery_enabled":%s,'
        '"session_timeout_seconds":%s,'
        '"rate_limit_window_seconds":%s,'
        '"rate_limit_max_requests":%s}\n'
    ) % (
        config.DEVICE_NAME,
        config.MODE,
        ip_address,
        uptime_seconds,
        free_memory,
        str(config.DISCOVERY_ENABLED).lower(),
        config.SESSION_TIMEOUT_SECONDS,
        config.RATE_LIMIT_WINDOW_SECONDS,
        config.RATE_LIMIT_MAX_REQUESTS,
    )


def discover_body(ip_address):
    return "DEVICE=%s;IP=%s;PORT=%s;MODE=%s\n" % (
        config.DEVICE_NAME,
        ip_address,
        config.HTTP_PORT,
        config.MODE,
    )


def fetch_text(path, ip_address, shared_token):
    if not auth.is_configured() or not auth.backend_token_is_valid(shared_token):
        raise OSError("local backend token rejected")

    if path == "/" or path == "/status":
        return status_body(ip_address)
    if path == "/api":
        return api_body()
    if path == "/health" or path == "/diagnostics":
        return diagnostics_body(ip_address)
    if path == "/discover":
        return discover_body(ip_address)
    raise OSError("local backend path not found")


def run_load_test(path, ip_address, request_count=10):
    successes = 0
    failures = 0
    started = ticks_ms()

    for _ in range(request_count):
        try:
            fetch_text(path, ip_address, auth.backend_token())
            successes += 1
        except Exception:
            failures += 1

    elapsed_ms = ticks_diff(ticks_ms(), started)

    return {
        "requests": request_count,
        "successes": successes,
        "failures": failures,
        "elapsed_ms": elapsed_ms,
    }
