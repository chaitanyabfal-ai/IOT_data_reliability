import json
import os
from typing import Any, Mapping
from urllib import request

from . import config


def fetch_on_prem_data(
    server_ip: str | None = None,
    server_port: str | int | None = None,
    endpoint: str | None = None,
    protocol: str | None = None,
) -> dict[str, Any]:
    """Fetch JSON data from an on-prem server configured via environment variables."""
    url = config.get_on_prem_server_url(
        server_ip=server_ip,
        server_port=server_port,
        endpoint=endpoint or os.getenv("ON_PREM_DATA_ENDPOINT", "/api/data"),
        protocol=protocol,
    )

    req = request.Request(url, headers={"Accept": "application/json"})
    timeout = int(os.getenv("ON_PREM_REQUEST_TIMEOUT", "10"))
    try:
        with request.urlopen(req, timeout=timeout) as response:
            payload = response.read()
    except TypeError:
        with request.urlopen(req) as response:
            payload = response.read()

    if not payload:
        return {}

    data = json.loads(payload.decode("utf-8"))
    if isinstance(data, Mapping):
        return dict(data)
    return data
