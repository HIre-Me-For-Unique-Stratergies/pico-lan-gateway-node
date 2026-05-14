def page_style():
    return """
*{box-sizing:border-box}
body{
margin:0;
min-height:100vh;
font-family:Arial,Helvetica,sans-serif;
color:#e7fbff;
background:#070912;
}
body:before{
content:"";
position:fixed;
inset:0;
z-index:-1;
background:
linear-gradient(rgba(0,255,234,.06) 1px,transparent 1px),
linear-gradient(90deg,rgba(255,42,231,.06) 1px,transparent 1px);
background-size:36px 36px;
}
main{max-width:900px;margin:0 auto;padding:28px}
.shell{
border:1px solid #23f6ff;
background:rgba(7,9,18,.9);
box-shadow:0 0 28px rgba(35,246,255,.18),inset 0 0 28px rgba(255,42,231,.06);
padding:24px;
}
.topbar{display:flex;gap:14px;align-items:flex-start;justify-content:space-between;margin-bottom:20px}
.admin-nav{
display:flex;
gap:8px;
align-items:center;
flex-wrap:wrap;
justify-content:flex-end;
max-width:520px;
}
.admin-nav a{
display:inline-block;
padding:9px 11px;
font-size:12px;
text-transform:uppercase;
}
.admin-nav .logout{border-color:#334056;color:#8fb8c0}
.eyebrow{margin:0 0 8px;color:#23f6ff;font-size:12px;text-transform:uppercase}
h1{margin:0;font-size:30px;line-height:1.05;color:#e7fbff;text-shadow:2px 0 #ff2ae7,-2px 0 #23f6ff}
h2{margin:24px 0 10px;font-size:16px;color:#23f6ff}
p{color:#b7dbe1;line-height:1.45}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:20px}
a,.button{
display:block;
padding:14px 16px;
border:1px solid #23f6ff;
color:#fff;
text-decoration:none;
background:#0b1020;
}
a:hover,.button:hover{border-color:#ff2ae7;color:#ffb7f6}
code,.value{background:#10172d;padding:2px 6px;color:#23f6ff}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:18px}
.stat{border:1px solid #26364f;background:#0b1020;padding:14px}
.label{display:block;color:#8fb8c0;font-size:12px;text-transform:uppercase}
.number{display:block;margin-top:6px;font-size:24px;color:#23f6ff}
pre{overflow:auto;padding:14px;border:1px solid #26364f;background:#050814;color:#e7fbff}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{padding:8px;border:1px solid #26364f;text-align:left;font-size:13px}
th{color:#23f6ff;background:#0b1020}
@media(max-width:640px){
.topbar{display:block}
.admin-nav{justify-content:flex-start;margin-top:14px}
.admin-nav a{flex:1 1 130px;text-align:center}
}
"""


def portal_page(title, action, button_text, error_html="", password_hint="", csrf_token=""):
    hidden = ""
    if csrf_token:
        hidden = '<input type="hidden" name="csrf_token" value="%s">' % escape_html(csrf_token)

    return """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
%s
body{display:grid;place-items:center;overflow:hidden}
body:before{
z-index:auto;
}
.portal{
position:relative;
width:min(92vw,420px);
padding:28px;
border:1px solid #23f6ff;
background:rgba(7,9,18,.88);
box-shadow:0 0 28px rgba(35,246,255,.25),inset 0 0 28px rgba(255,42,231,.08);
}
.portal:before{
content:"";
position:absolute;
inset:8px;
border:1px solid rgba(255,42,231,.45);
pointer-events:none;
}
.eyebrow{
margin:0 0 8px;
color:#23f6ff;
font-size:12px;
letter-spacing:0;
text-transform:uppercase;
}
h1{
margin:0 0 20px;
font-size:30px;
line-height:1.05;
text-shadow:2px 0 #ff2ae7,-2px 0 #23f6ff;
}
label{
display:block;
margin:14px 0 6px;
font-size:13px;
color:#a7f8ff;
}
input{
width:100%%;
padding:12px;
border:1px solid #23f6ff;
background:#090d1b;
color:#ffffff;
font-size:16px;
outline:none;
}
input:focus{
border-color:#ff2ae7;
box-shadow:0 0 14px rgba(255,42,231,.35);
}
button{
width:100%%;
margin-top:20px;
padding:13px;
border:0;
background:#23f6ff;
color:#071018;
font-weight:bold;
font-size:15px;
text-transform:uppercase;
cursor:pointer;
}
button:hover{background:#ff2ae7;color:#fff}
.error{
margin:0 0 10px;
padding:10px;
border-left:3px solid #ff2a6d;
background:rgba(255,42,109,.14);
color:#ffd9e4;
font-size:13px;
}
.hint{
margin:16px 0 0;
font-size:12px;
color:#8fb8c0;
}
main{padding:0}
</style>
</head>
<body>
<main class="portal">
<p class="eyebrow">LAN Gateway Node</p>
<h1>%s</h1>
%s
<form action="%s" method="post">
<label for="username">Admin username</label>
<input id="username" name="username" value="admin" autocomplete="username" required>
<label for="password">Access password</label>
<input id="password" name="password" type="password" autocomplete="current-password" required>
%s
<button type="submit">%s</button>
</form>
<p class="hint">%s</p>
</main>
</body>
</html>
""" % (
        title,
        page_style().replace("%", "%%"),
        title,
        error_html,
        action,
        hidden,
        button_text,
        password_hint,
    )


def login_page(error=False, csrf_token="", message=""):
    error_html = ""
    if error:
        if not message:
            message = "Access denied. Check the admin credentials."
        error_html = '<p class="error">%s</p>' % escape_html(message)

    return portal_page(
        "Portal Access",
        "/login",
        "Enter Gateway",
        error_html,
        "Local portal. Use only on your trusted LAN or behind HTTPS termination.",
        csrf_token,
    )


def setup_page(error=False, csrf_token=""):
    error_html = ""
    if error:
        error_html = '<p class="error">Use a password with at least 8 characters.</p>'

    return portal_page(
        "First Run Setup",
        "/setup",
        "Create Admin",
        error_html,
        "Session, client, and internal backend tokens are generated automatically.",
        csrf_token,
    )


def setup_complete_page():
    return info_page(
        "Setup Complete",
        "Admin credentials and local access tokens were created. The current browser session can continue.",
        "",
        None,
    )


def discovery_rows(message):
    rows = ""
    for part in message.split(";"):
        key_value = part.split("=", 1)
        if len(key_value) == 2:
            rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
                key_value[0],
                key_value[1],
            )

    return rows


def metric_rows(data):
    rows = ""
    for key in sorted(data):
        rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
            key.replace("_", " "),
            data[key],
        )

    return rows


def request_log_rows(entries):
    if not entries:
        return "<p>No requests logged yet.</p>"

    rows = ""
    for entry in entries:
        rows += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            escape_html(str(entry["client_ip"])),
            escape_html(str(entry["method"])),
            escape_html(str(entry["path"])),
            escape_html(str(entry["status"])),
        )

    return (
        "<table><thead><tr><th>Client</th><th>Method</th><th>Path</th><th>Status</th></tr></thead>"
        "<tbody>%s</tbody></table>"
    ) % rows


def escape_html(value):
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def dashboard_page(ip_address, discovery_message, metric_data, request_log, session_seconds):
    return """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LAN Gateway Node</title>
<style>
%s
</style>
</head>
<body>
<main>
<section class="shell">
<div class="topbar">
<div>
<h1>LAN Gateway Node</h1>
</div>
<nav class="admin-nav" aria-label="Admin Console">
<a href="/">Dashboard</a>
<a class="logout" href="/logout">Logout</a>
</nav>
</div>
<p>Gateway <code>%s</code> is online on this device. Select a protected route.</p>
<section class="grid">
<a href="/test/start">Run Load Test</a>
<a href="/backend">Backend Data</a>
<a href="/status">Backend Status</a>
<a href="/api">Backend API</a>
<a href="/health">Health</a>
<a href="/export">Export Status</a>
</section>
<h2>Gateway Metrics</h2>
<section class="stats">%s</section>
<h2>Session</h2>
<section class="stats"><div class="stat"><span class="label">seconds remaining</span><span class="number">%s</span></div></section>
<h2>Gateway Identity</h2>
<section class="stats">%s</section>
<h2>Discovery Message</h2>
<pre>%s</pre>
<h2>Request Log</h2>
%s
</section>
</main>
</body>
</html>
""" % (
        page_style().replace("%", "%%"),
        ip_address,
        metric_rows(metric_data),
        session_seconds,
        discovery_rows(discovery_message),
        discovery_message,
        request_log_rows(request_log),
    )


def metrics_page(data, request_log):
    return info_page(
        "Gateway Metrics",
        "Current counters, diagnostics, and recent requests.",
        metric_rows(data),
        None,
        "<h2>Request Log</h2>%s" % request_log_rows(request_log),
    )


def backend_summary_page(status_text, api_text):
    raw = (
        "<h2>Status Data</h2><pre>%s</pre>"
        "<h2>API Data</h2><pre>%s</pre>"
    ) % (escape_html(status_text), escape_html(api_text))

    return info_page(
        "Backend Data",
        "Gateway-rendered view of protected backend data.",
        "",
        None,
        raw,
    )


def backend_data_page(title, subtitle, raw_text):
    return info_page(title, subtitle, "", escape_html(raw_text))


def load_test_page(result):
    rows = ""
    for key in ("requests", "successes", "failures", "elapsed_ms"):
        rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
            key.replace("_", " "),
            result[key],
        )

    return info_page("Load Test Result", "Backend load test completed.", rows, None)


def info_page(title, subtitle, stat_rows, raw_text, extra_html=""):
    raw = ""
    if raw_text:
        raw = "<h2>Raw Output</h2><pre>%s</pre>" % raw_text

    stats = ""
    if stat_rows:
        stats = '<section class="stats">%s</section>' % stat_rows

    return """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<style>
%s
</style>
</head>
<body>
<main>
<section class="shell">
<div class="topbar">
<div>
<p class="eyebrow">LAN Gateway Node</p>
<h1>%s</h1>
</div>
<nav class="admin-nav" aria-label="Admin Console">
<a href="/">Dashboard</a>
<a class="logout" href="/logout">Logout</a>
</nav>
</div>
<p>%s</p>
%s
%s
%s
</section>
</main>
</body>
</html>
""" % (
        title,
        page_style().replace("%", "%%"),
        title,
        subtitle,
        stats,
        raw,
        extra_html,
    )
