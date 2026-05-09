import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import pytest


PROBE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "alpaca_lan_probe.py"
_SPEC = importlib.util.spec_from_file_location("alpaca_lan_probe", PROBE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
probe = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = probe
_SPEC.loader.exec_module(probe)


def test_build_management_devices_url_plain_host_port():
    url = probe.build_management_devices_url(protocol="http", address="192.168.1.10:32323")
    assert url == "http://192.168.1.10:32323/management/v1/configureddevices"


def test_build_management_devices_url_full_base():
    url = probe.build_management_devices_url(protocol="http", address="http://10.0.0.5:32323")
    assert url == "http://10.0.0.5:32323/management/v1/configureddevices"


def test_parse_dotenv_reads_keys(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text('ALPACA_ADDRESS=1.2.3.4:32323\n# c\nFOO=bar\n', encoding="utf-8")
    data = probe._parse_dotenv(p)
    assert data["ALPACA_ADDRESS"] == "1.2.3.4:32323"
    assert data["FOO"] == "bar"


def test_main_success_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ALPACA_ADDRESS=127.0.0.1:32323\nALPACA_PROTOCOL=http\n", encoding="utf-8")
    payload = [{"DeviceType": "Telescope", "DeviceName": "Seestar", "DeviceNumber": 0}]
    body = __import__("json").dumps(payload).encode("utf-8")

    class FakeResponse:
        status = 200

        def read(self) -> bytes:
            return body

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *exc: object) -> None:  # noqa: ANN401
            return None

    monkeypatch.setattr(probe, "urlopen", lambda *_a, **_k: FakeResponse())

    monkeypatch.setattr(sys, "argv", ["alpaca_lan_probe.py", "--env-file", str(env_file)])
    assert probe.main() == 0


def test_main_missing_address(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env_file = tmp_path / ".env"
    env_file.write_text("ALPACA_ENABLED=true\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["alpaca_lan_probe.py", "--env-file", str(env_file)])
    assert probe.main() == 2


def test_main_http_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from urllib.error import HTTPError

    env_file = tmp_path / ".env"
    env_file.write_text("ALPACA_ADDRESS=10.0.0.1:32323\n", encoding="utf-8")

    def boom(*_a: object, **_k: object) -> None:
        raise HTTPError("http://x", 500, "err", hdrs=None, fp=BytesIO())

    monkeypatch.setattr(probe, "urlopen", boom)
    monkeypatch.setattr(sys, "argv", ["alpaca_lan_probe.py", "--env-file", str(env_file)])
    assert probe.main() == 1
