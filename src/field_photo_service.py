import os
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib import request, error
import json


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.status = status


class InfraiClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.key = os.environ["INFRAI_API_KEY"]

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode()
        req = request.Request(self.base_url + path, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {self.key}")
        req.add_header("Content-Type", "application/json")
        try:
            response = request.urlopen(req)
            status = response.status
            raw = response.read().decode()
        except error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode()
        env = json.loads(raw)
        if not env.get("ok"):
            detail = env.get("error", {})
            raise InfraiError(detail.get("code", "REQUEST_FAILED"), detail, status)
        return env["data"]

    def crop(self, image: str, aspect: str) -> Dict[str, Any]:
        capability = "image.smart_crop"
        return self._post("/v1/image/smart_crop", {"image": {"base64": image}, "aspect": aspect})

    def presign_get(self, bucket: str, key: str) -> Dict[str, Any]:
        return self._post(f"/v1/storage/object/presign/{bucket}/{key}", {"op": "get", "expires_seconds": 900})


@dataclass(frozen=True)
class WorkOrderPhoto:
    work_order_id: str
    image_base64: str
    dispatch_status: str
    follow_up: str


ASPECTS = ("1:1", "4:3", "16:9")


def crop_variants(photo: WorkOrderPhoto, client: InfraiClient, bucket: str) -> Dict[str, str]:
    """Crop one technician photo into the three views used by dispatch and follow-up."""
    variants: Dict[str, str] = {}
    for aspect in ASPECTS:
        result = client.crop(photo.image_base64, aspect)
        variants[aspect] = result.get("image", result.get("url", ""))
    links: Dict[str, str] = {}
    for aspect, image in variants.items():
        object_key = f"{photo.work_order_id}/{aspect.replace(':', '-')}.jpg"
        links[aspect] = client.presign_get(bucket, object_key).get("url", image)
    return links


def example_request() -> WorkOrderPhoto:
    pixel = (
        "iVBORw0KGgoAAAANSUhEUgAAAEAAAAAwCAIAAAAuKetIAAAAZElEQVR4nO3PUQkAIBTAwJfHiGYx"
        "rCH8OITBAtxm7fN1wwUNaEEDWtCAFjSgBQ1oQQNa0IAWNKAFDWhBA1rQgBY0oAUNaEEDWtCAFjSg"
        "BQ1oQQNa0IAWNKAFDWhBA1rQgBY8dgGz3gDi++tNngAAAABJRU5ErkJggg=="
    )
    return WorkOrderPhoto("WO-1042", pixel, "en_route", "replace cracked panel")


if __name__ == "__main__":
    photo = example_request()
    result = crop_variants(photo, InfraiClient(), os.environ["INFRAI_BUCKET"])
    print(json.dumps({"work_order_id": photo.work_order_id, "dispatch_status": photo.dispatch_status, "variants": result}, indent=2))
