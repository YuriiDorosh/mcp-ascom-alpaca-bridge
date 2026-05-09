from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class ITelescopeVideoStreamRelay(ABC):
    """Domain port: relay telescope video as a sequence of still JPEG frames (e.g. from RTSP)."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether a video source URL is configured and streaming may be attempted."""

    @abstractmethod
    async def subscribe_jpeg_frames(self) -> AsyncIterator[bytes]:
        """Yield sequential JPEG-encoded frames while subscriptions are active."""

        ...


