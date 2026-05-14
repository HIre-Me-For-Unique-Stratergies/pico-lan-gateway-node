import time

import config


def _line_count(lines):
    return len(lines)


def _read_lines():
    try:
        with open(config.AUDIT_LOG_FILE) as handle:
            return handle.readlines()
    except OSError:
        return []


def _write_lines(lines):
    with open(config.AUDIT_LOG_FILE, "w") as handle:
        for line in lines:
            handle.write(line)


def append(client_ip, method, path, status):
    line = "%s client=%s method=%s path=%s status=%s\n" % (
        int(time.time()),
        client_ip,
        method,
        path,
        status,
    )

    try:
        lines = _read_lines()
        lines.append(line)

        max_lines = getattr(config, "AUDIT_LOG_MAX_LINES", 100)
        if _line_count(lines) > max_lines:
            lines = lines[-max_lines:]

        _write_lines(lines)
    except OSError:
        pass


def tail(limit=25):
    lines = _read_lines()
    if limit <= 0:
        return []
    return [line.strip() for line in lines[-limit:]]
