"""Starts the Smart Screen web server.

Run it from this folder:    py run_server.py        (Windows)
                            python3 run_server.py   (Linux, macOS)
Stop it with Ctrl+C.
"""
from server.app import create_app
from server.config import ServerConfig


def main() -> None:
    config = ServerConfig()
    app = create_app(config)
    print(f"Smart Screen server: http://localhost:{config.port}")
    # threaded=True: each connected page gets its own thread, so one page that keeps a
    # connection open does not block the others.
    app.run(host=config.host, port=config.port, threaded=True)


if __name__ == "__main__":
    main()
