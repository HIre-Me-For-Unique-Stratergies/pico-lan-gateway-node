import time


START_TIME = time.time()

COUNTERS = {
    "allowed_requests": 0,
    "blocked_requests": 0,
    "proxied_requests": 0,
    "proxy_failures": 0,
    "load_test_requests": 0,
    "load_test_successes": 0,
    "load_test_failures": 0,
}


def increment(name, amount=1):
    COUNTERS[name] = COUNTERS.get(name, 0) + amount


def snapshot():
    data = {
        "uptime_seconds": int(time.time() - START_TIME),
    }
    data.update(COUNTERS)
    return data


def as_text():
    data = snapshot()
    lines = []

    for key in sorted(data):
        lines.append("%s=%s" % (key, data[key]))

    return "\n".join(lines) + "\n"
