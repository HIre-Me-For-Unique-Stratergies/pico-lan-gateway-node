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
linear-gradient(90deg,rgba(255,42,231,.06) 1px,transparent 1px),
radial-gradient(circle at 20% 20%,rgba(0,255,234,.22),transparent 28%),
radial-gradient(circle at 82% 70%,rgba(255,42,231,.16),transparent 30%);
background-size:36px 36px,36px 36px,100% 100%,100% 100%;
}
main{max-width:900px;margin:0 auto;padding:28px}
.shell{
border:1px solid #23f6ff;
background:rgba(7,9,18,.9);
box-shadow:0 0 28px rgba(35,246,255,.18),inset 0 0 28px rgba(255,42,231,.06);
padding:24px;
}
.topbar{display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:20px}
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
.logout{border-color:#334056;color:#8fb8c0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:18px}
.stat{border:1px solid #26364f;background:#0b1020;padding:14px}
.label{display:block;color:#8fb8c0;font-size:12px;text-transform:uppercase}
.number{display:block;margin-top:6px;font-size:24px;color:#23f6ff}
pre{overflow:auto;padding:14px;border:1px solid #26364f;background:#050814;color:#e7fbff}
"""


def login_page(error=False):
    error_html = ""
    if error:
        error_html = '<p class="error">Access denied. Check the admin credentials.</p>'

    return """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Gateway Portal Login</title>
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
<h1>Portal Access</h1>
%s
<form action="/login" method="get">
<label for="username">Admin username</label>
<input id="username" name="username" autocomplete="username" required>
<label for="password">Access password</label>
<input id="password" name="password" type="password" autocomplete="current-password" inputmode="numeric" required>
<button type="submit">Enter Gateway</button>
</form>
<p class="hint">Local HTTP portal. Use only on your trusted LAN.</p>
</main>
</body>
</html>
""" % (page_style().replace("%", "%%"), error_html)


def dashboard_page(ip_address):
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
<p class="eyebrow">Admin Console</p>
<h1>LAN Gateway Node</h1>
</div>
<a class="logout" href="/logout">Logout</a>
</div>
<p>Gateway <code>%s</code> is online. Select a protected route.</p>
<section class="grid">
<a href="/discover">Gateway Discovery</a>
<a href="/metrics">Gateway Metrics</a>
<a href="/test/start">Run Load Test</a>
<a href="/backend">Backend Page</a>
<a href="/status">Backend Status</a>
<a href="/api">Backend API</a>
</section>
</section>
</main>
</body>
</html>
""" % (page_style().replace("%", "%%"), ip_address)


def discover_page(message):
    rows = ""
    for part in message.split(";"):
        key_value = part.split("=", 1)
        if len(key_value) == 2:
            rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
                key_value[0],
                key_value[1],
            )

    return info_page("Gateway Discovery", "Broadcast identity for this gateway node.", rows, message)


def metrics_page(data):
    rows = ""
    for key in sorted(data):
        rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
            key.replace("_", " "),
            data[key],
        )

    return info_page("Gateway Metrics", "Current counters and diagnostics.", rows, None)


def load_test_page(result):
    rows = ""
    for key in ("requests", "successes", "failures", "elapsed_ms"):
        rows += '<div class="stat"><span class="label">%s</span><span class="number">%s</span></div>' % (
            key.replace("_", " "),
            result[key],
        )

    return info_page("Load Test Result", "Backend load test completed.", rows, None)


def info_page(title, subtitle, stat_rows, raw_text):
    raw = ""
    if raw_text:
        raw = "<h2>Raw Output</h2><pre>%s</pre>" % raw_text

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
<a class="logout" href="/">Dashboard</a>
</div>
<p>%s</p>
<section class="stats">%s</section>
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
        stat_rows,
        raw,
    )
