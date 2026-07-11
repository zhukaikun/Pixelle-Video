"""
Custom Relay Video Generation Client (Sora-style API)

For third-party relay services (e.g. new-api) that expose video generation
through the OpenAI Sora-compatible async task API.

Flow:
1. Submit task  -> POST {base_url}/v1/videos
2. Poll status   -> GET  {base_url}/v1/videos/{task_id}
3. Download video -> GET  {base_url}/v1/videos/{task_id}/content

Configure via the ``custom`` provider section in config.yaml or Web UI.
"""

import os
import time
import logging
import requests
import base64
from typing import Optional

logger = logging.getLogger(__name__)


class CustomVideoClient:
    """
    Video generation client for third-party relay services.

    Uses the Sora-style async task API compatible with new-api:
    POST /v1/videos, GET /v1/videos/{id}, GET /v1/videos/{id}/content
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        local_proxy: Optional[str] = None,
        timeout: int = 120,
    ) -> None:
        self.api_key = api_key or os.getenv("CUSTOM_API_KEY")
        _base = (base_url or os.getenv("CUSTOM_BASE_URL") or "").rstrip("/")
        if _base.endswith("/v1"):
            _base = _base[:-3]
        self.base_url = _base
        self.local_proxy = local_proxy
        self.timeout = timeout

        if not self.api_key:
            logger.warning("CustomVideoClient: CUSTOM_API_KEY not set")
        if not self.base_url:
            logger.warning("CustomVideoClient: CUSTOM_BASE_URL not set")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
        }

    def _proxies(self) -> Optional[dict]:
        if not self.local_proxy:
            return None
        return {"http": self.local_proxy, "https": self.local_proxy}

    def generate_video(
        self,
        prompt: str,
        image_path: Optional[str],
        save_path: str,
        model: str = "sora-1",
        duration: int = 5,
        **kwargs,
    ) -> str:
        """
        Generate video through relay service (Sora-style API).

        Args:
            prompt: Video description prompt
            image_path: Input image for image-to-video; None for text-to-video
            save_path: Output video save path
            model: Model name (e.g. sora-1, doubao-seedance-2-0-260128)
            duration: Video duration in seconds
        """
        if not self.api_key:
            raise RuntimeError(
                "CUSTOM_API_KEY not set. "
                "Configure it in the custom provider section of config.yaml or Web UI."
            )
        if not self.base_url:
            raise RuntimeError(
                "CUSTOM_BASE_URL not set. "
                "Configure it in the custom provider section of config.yaml or Web UI."
            )

        task_id = self._submit_task(prompt, image_path, model, duration, **kwargs)
        self._poll_until_done(task_id)
        self._download_video(task_id, save_path)

        return save_path

    def _submit_task(self, prompt: str, image_path: Optional[str], model: str, duration: int, **kwargs) -> str:
        url = f"{self.base_url}/v1/videos"

        payload = {
            "model": model,
            "prompt": prompt,
        }

        if image_path:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Input image not found: {image_path}")
            with open(image_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode("utf-8")
            ext = os.path.splitext(image_path)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            payload["image"] = f"data:{mime};base64,{img_data}"

        metadata = {"duration": duration}

        video_ratio = kwargs.get("video_ratio") or kwargs.get("ratio")
        if video_ratio:
            metadata["ratio"] = video_ratio

        resolution = kwargs.get("resolution")
        if resolution:
            metadata["resolution"] = resolution

        for key in ["seed", "watermark", "generate_audio", "negative_prompt", "style", "quality_level"]:
            if key in kwargs and kwargs[key] is not None:
                metadata[key] = kwargs[key]

        payload["metadata"] = metadata

        headers = self._headers()
        headers["Content-Type"] = "application/json"

        logger.info(f"CustomVideoClient: submitting task model={model}, duration={duration}s, payload={payload}")
        resp = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
            proxies=self._proxies(),
        )

        if not resp.ok:
            logger.error(f"Custom video task submit failed: {resp.text}")
            resp.raise_for_status()

        data = resp.json()
        task_id = data.get("id")
        if not task_id:
            raise RuntimeError(f"Custom video API did not return task ID: {data}")

        logger.info(f"CustomVideoClient: task submitted, id={task_id}")
        return task_id

    def _poll_until_done(self, task_id: str, max_polls: int = 120, interval: int = 5) -> dict:
        url = f"{self.base_url}/v1/videos/{task_id}"

        for i in range(max_polls):
            resp = requests.get(url, headers=self._headers(), timeout=30, proxies=self._proxies())
            resp.raise_for_status()
            data = resp.json()

            status = data.get("status")
            progress = data.get("progress", 0)

            if status in ("completed", "succeeded"):
                logger.info(f"CustomVideoClient: task completed, id={task_id}")
                return data
            elif status in ("failed", "expired", "cancelled"):
                error_msg = (
                    data.get("error", {}).get("message")
                    if isinstance(data.get("error"), dict)
                    else str(data.get("error"))
                ) or data.get("message") or "Unknown error"
                raise RuntimeError(f"Custom video generation {status}: {error_msg}")

            logger.debug(f"CustomVideoClient: polling task={task_id}, status={status}, progress={progress}%, poll={i+1}")
            time.sleep(interval)

        raise TimeoutError(f"Custom video generation timeout (task_id={task_id})")

    def _download_video(self, task_id: str, save_path: str):
        url = f"{self.base_url}/v1/videos/{task_id}/content"
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

        resp = requests.get(url, headers=self._headers(), stream=True, timeout=120, proxies=self._proxies())
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "video" not in content_type and "application/octet-stream" not in content_type:
            raise RuntimeError(f"Unexpected content type for video download: {content_type}, body: {resp.text[:500]}")

        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"CustomVideoClient: video saved: {save_path}")

    @staticmethod
    def _resolution_to_dimensions(resolution: str, ratio: Optional[str] = None) -> tuple[Optional[int], Optional[int]]:
        res_map = {
            "480p": 480,
            "720p": 720,
            "1080p": 1080,
            "2k": 1440,
            "4k": 2160,
        }
        base = res_map.get(resolution.lower(), 720)
        ratio_map = {
            "16:9": (base * 16 // 9, base),
            "9:16": (base, base * 9 // 16),
            "4:3": (base * 4 // 3, base),
            "3:4": (base, base * 3 // 4),
            "1:1": (base, base),
        }
        if ratio and ratio in ratio_map:
            return ratio_map[ratio]
        return (base * 16 // 9, base)
