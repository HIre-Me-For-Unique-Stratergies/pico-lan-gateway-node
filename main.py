import sys


APP_DIR = "gateway_pico"
APP_ENTRY = "main.py"


def _add_app_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)


def _find_app_entry():
    for app_dir in (APP_DIR, "/" + APP_DIR):
        app_path = app_dir + "/" + APP_ENTRY

        try:
            handle = open(app_path)
            handle.close()
            _add_app_path(app_dir)
            return app_path
        except OSError:
            pass

    raise OSError("Cannot find %s/%s" % (APP_DIR, APP_ENTRY))


def run():
    app_path = _find_app_entry()

    namespace = {
        "__name__": "__main__",
        "__file__": app_path,
    }

    with open(app_path) as handle:
        exec(handle.read(), namespace)


run()
