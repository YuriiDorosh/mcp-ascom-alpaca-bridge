from collections.abc import AsyncIterator

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from domain.ports.telescope_video_stream import ITelescopeVideoStreamRelay
from logic.init import init_container

router = APIRouter(tags=['telescope-video'])

_BOUNDARY_PREFIX = b'--frame'


async def _mjpeg_multipart_body(relay: ITelescopeVideoStreamRelay) -> AsyncIterator[bytes]:
    async for jpeg in relay.subscribe_jpeg_frames():
        header = (
            _BOUNDARY_PREFIX
            + b'\r\nContent-Type: image/jpeg\r\nContent-Length: '
            + str(len(jpeg)).encode('ascii')
            + b'\r\n\r\n'
        )
        yield header + jpeg + b'\r\n'


@router.get('/stream')
async def telescope_video_mjpeg_stream() -> StreamingResponse:
    """MJPEG multipart stream bridged from the configured RTSP source (JPEG over HTTP)."""

    container = init_container()
    relay = container.resolve(ITelescopeVideoStreamRelay)
    if not relay.is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                'Telescope RTSP stream is unavailable: set TELESCOPE_RTSP_URL in the backend environment.'
            ),
        )

    return StreamingResponse(
        _mjpeg_multipart_body(relay),
        media_type='multipart/x-mixed-replace; boundary=frame',
    )
