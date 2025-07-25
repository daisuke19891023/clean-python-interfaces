from typing import Any

class Config:
    LOGGING_CONFIG: dict[str, Any]

config: Config

def run(
    app: Any,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    uds: str | None = None,
    fd: int | None = None,
    loop: str = "auto",
    http: str = "auto",
    ws: str = "auto",
    ws_max_size: int = 16777216,
    ws_ping_interval: float | None = 20.0,
    ws_ping_timeout: float | None = 20.0,
    ws_per_message_deflate: bool = True,
    lifespan: str = "auto",
    interface: str = "auto",
    debug: bool = False,
    reload: bool = False,
    reload_dirs: list[str] | None = None,
    reload_includes: list[str] | None = None,
    reload_excludes: list[str] | None = None,
    reload_delay: float = 0.25,
    workers: int | None = None,
    env_file: str | None = None,
    log_config: dict[str, Any] | str | None = None,
    log_level: str | None = None,
    access_log: bool = True,
    proxy_headers: bool = True,
    server_header: bool = True,
    date_header: bool = True,
    forwarded_allow_ips: str | None = None,
    root_path: str = "",
    limit_concurrency: int | None = None,
    limit_max_requests: int | None = None,
    backlog: int = 2048,
    timeout_keep_alive: int = 5,
    timeout_notify: int = 30,
    callback_notify: Any = None,
    ssl_keyfile: str | None = None,
    ssl_certfile: str | None = None,
    ssl_keyfile_password: str | None = None,
    ssl_version: int = 17,
    ssl_cert_reqs: int = 0,
    ssl_ca_certs: str | None = None,
    ssl_ciphers: str = "TLSv1",
    headers: list[list[str]] | None = None,
    use_colors: bool | None = None,
    app_dir: str | None = None,
    factory: bool = False,
) -> None: ...
