from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from punq import Container

from application.api.telescope import video_stream as video_stream_module
from application.api.telescope.video_stream import router as telescope_video_router
from domain.ports.telescope_video_stream import ITelescopeVideoStreamRelay


class _RelayOff(ITelescopeVideoStreamRelay):
    def is_configured(self) -> bool:
        return False

    async def subscribe_jpeg_frames(self) -> AsyncIterator[bytes]:
        if False:
            yield b''


class _RelayOn(ITelescopeVideoStreamRelay):
    def is_configured(self) -> bool:
        return True

    async def subscribe_jpeg_frames(self) -> AsyncIterator[bytes]:
        yield b'h264-is-not-involved'


def _app_with_stub_relay(monkeypatch, relay: ITelescopeVideoStreamRelay) -> TestClient:
    container = Container()
    container.register(ITelescopeVideoStreamRelay, instance=relay)
    monkeypatch.setattr(video_stream_module, 'init_container', lambda: container)

    app = FastAPI()
    app.include_router(telescope_video_router, prefix='/api/v1/telescope')
    return TestClient(app)


def test_telescope_stream_returns_503_when_not_configured(monkeypatch):
    client = _app_with_stub_relay(monkeypatch, _RelayOff())
    r = client.get('/api/v1/telescope/stream')
    assert r.status_code == 503


def test_telescope_stream_returns_multipart_when_configured(monkeypatch):
    client = _app_with_stub_relay(monkeypatch, _RelayOn())
    r = client.get('/api/v1/telescope/stream')
    assert r.status_code == 200
    ctype = r.headers.get('content-type', '')
    assert 'multipart/x-mixed-replace' in ctype
    assert 'boundary=frame' in ctype
    assert b'Content-Type: image/jpeg' in r.content
    assert b'Content-Length:' in r.content
    assert b'h264-is-not-involved' in r.content
