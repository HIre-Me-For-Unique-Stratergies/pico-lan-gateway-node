import config


ALLOW = "allow"
BLOCK = "block"
DENY = "deny"


def _path_matches(rule_path, request_path):
    if rule_path == "*":
        return True
    return rule_path == request_path


def _source_matches(rule_source, client_ip):
    if rule_source == "ANY":
        return True
    return rule_source == client_ip


def check(client_ip, path):
    for rule_source, rule_path, action in config.RULES:
        if _source_matches(rule_source, client_ip) and _path_matches(rule_path, path):
            return action

    return config.DEFAULT_ACTION


def is_allowed(client_ip, path):
    return check(client_ip, path) == ALLOW
