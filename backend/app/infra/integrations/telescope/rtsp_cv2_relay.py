from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from domain.ports.telescope_video_stream import ITelescopeVideoStreamRelay
from settings.config import Config

logger = logging.getLogger(__name__)

# Sentinel to unblock consumer tasks when unsubscribing or when the producer stops.
_EOF = None


def _import_cv2_after_env(config: Config):
    if config.telescope_rtsp_transport_tcp:
        os.environ.setdefault('OPENCV_FFMPEG_CAPTURE_OPTIONS', 'rtsp_transport;tcp')
    import cv2

    return cv2


class Cv2RtspTelescopeVideoRelay(ITelescopeVideoStreamRelay):
    """OpenCV-based RTSP capture with reconnect, optional resize, and JPEG encoding."""

    def __init__(self, *, config: Config) -> None:
        self._config = config
        self._cv2 = _import_cv2_after_env(config)
        self._lock = asyncio.Lock()
        self._queues: list[asyncio.Queue[bytes | None]] = []
        self._producer: asyncio.Task[None] | None = None

    def is_configured(self) -> bool:
        url = (self._config.telescope_rtsp_url or '').strip()
        return bool(url)

    async def subscribe_jpeg_frames(self) -> AsyncIterator[bytes]:
        queue: asyncio.Queue[bytes | None] = asyncio.Queue(maxsize=2)

        async with self._lock:
            self._queues.append(queue)
            if self._producer is None or self._producer.done():
                self._producer = asyncio.create_task(self._producer_loop(), name='rtsp-mjpeg-producer')

        try:
            while True:
                item = await queue.get()
                if item is _EOF:
                    break
                yield item
        finally:
            await self._unregister_queue(queue)

    async def _unregister_queue(self, queue: asyncio.Queue[bytes | None]) -> None:
        try:
            queue.put_nowait(_EOF)
        except asyncio.QueueFull:
            try:
                _ = queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(_EOF)
            except asyncio.QueueFull:
                pass

        producer_to_cancel: asyncio.Task[None] | None = None

        async with self._lock:
            try:
                self._queues.remove(queue)
            except ValueError:
                return
            if len(self._queues) == 0 and self._producer is not None:
                producer_to_cancel = self._producer
                self._producer = None

        if producer_to_cancel is not None:
            producer_to_cancel.cancel()
            try:
                await producer_to_cancel
            except asyncio.CancelledError:
                pass

    async def _broadcast_jpeg(self, jpeg: bytes) -> None:
        async with self._lock:
            targets = list(self._queues)

        for q in targets:
            try:
                q.put_nowait(jpeg)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(jpeg)
                except asyncio.QueueFull:
                    pass

    async def _signal_eof_to_all_queues(self) -> None:
        async with self._lock:
            targets = list(self._queues)

        for q in targets:
            try:
                q.put_nowait(_EOF)
            except asyncio.QueueFull:
                try:
                    _ = q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                try:
                    q.put_nowait(_EOF)
                except asyncio.QueueFull:
                    pass

    async def _producer_loop(self) -> None:
        cap: Any | None = None
        backoff = float(self._config.telescope_rtsp_reconnect_initial_seconds)
        url = (self._config.telescope_rtsp_url or '').strip()
        jpeg_params = [int(self._cv2.IMWRITE_JPEG_QUALITY), int(self._config.telescope_rtsp_jpeg_quality)]

        try:
            while True:
                async with self._lock:
                    has_clients = len(self._queues) > 0
                if not has_clients:
                    return

                if cap is None:
                    opened = False
                    if url:
                        cap = await asyncio.to_thread(self._open_capture, url)
                        opened = bool(cap is not None and await asyncio.to_thread(cap.isOpened))
                    if not opened:
                        await self._release_capture_async(cap)
                        cap = None
                        await asyncio.sleep(backoff)
                        backoff = min(
                            backoff * 2,
                            float(self._config.telescope_rtsp_reconnect_max_seconds),
                        )
                        continue

                    backoff = float(self._config.telescope_rtsp_reconnect_initial_seconds)

                frame = await asyncio.to_thread(self._read_frame_sync, cap)
                if frame is None:
                    await self._release_capture_async(cap)
                    cap = None
                    await asyncio.sleep(backoff)
                    backoff = min(
                        backoff * 2,
                        float(self._config.telescope_rtsp_reconnect_max_seconds),
                    )
                    continue

                jpeg = await asyncio.to_thread(self._encode_jpeg_sync, frame, jpeg_params)
                if jpeg:
                    await self._broadcast_jpeg(jpeg)
                    backoff = float(self._config.telescope_rtsp_reconnect_initial_seconds)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('RTSP MJPEG producer failed')
            await self._signal_eof_to_all_queues()
        finally:
            await self._release_capture_async(cap)

    def _open_capture(self, url: str):
        return self._cv2.VideoCapture(url, self._cv2.CAP_FFMPEG)

    def _read_frame_sync(self, cap: Any) -> Any | None:
        ok, frame = cap.read()
        if not ok or frame is None:
            return None
        return self._maybe_resize(frame)

    def _maybe_resize(self, frame: Any) -> Any:
        max_w = self._config.telescope_rtsp_max_frame_width
        if max_w is None or max_w <= 0:
            return frame
        h, w = frame.shape[:2]
        if w <= max_w:
            return frame
        scale = max_w / float(w)
        new_w = int(round(w * scale))
        new_h = int(round(h * scale))
        return self._cv2.resize(frame, (new_w, new_h), interpolation=self._cv2.INTER_AREA)

    def _encode_jpeg_sync(self, frame: Any, jpeg_params: list[int]) -> bytes | None:
        ok, buf = self._cv2.imencode('.jpg', frame, jpeg_params)
        if not ok or buf is None:
            return None
        return buf.tobytes()

    async def _release_capture_async(self, cap: Any | None) -> None:
        if cap is None:
            return
        await asyncio.to_thread(self._release_capture_sync, cap)

    def _release_capture_sync(self, cap: Any) -> None:
        try:
            cap.release()
        except Exception:
            logger.debug('VideoCapture.release failed', exc_info=True)
