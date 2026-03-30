"""
画像類似検索アクティビティ (Google Cloud Vision Web Detection)

アップロード画像の GCS URI を受け取り、
Cloud Vision API で同一・類似画像の掲載 URL を返す。
"""

import json
import os
from dataclasses import dataclass

from temporalio import activity


@dataclass
class ImageSearchInput:
    """画像検索の入力"""

    gcs_uri: str  # gs://bucket/path/to/image.jpg


@dataclass
class ImageSearchResult:
    """画像検索の出力"""

    results_json: str  # JSON 文字列


def _get_vision_credentials():
    """GCS_SA_KEY_BASE64 から credentials を取得する。"""
    import base64
    import json as _json

    from google.oauth2 import service_account

    key_b64 = os.getenv("GCS_SA_KEY_BASE64", "")
    if key_b64:
        decoded = base64.b64decode(key_b64)
        info = _json.loads(decoded.decode("utf-8"))
        return service_account.Credentials.from_service_account_info(info)
    return None


@activity.defn
async def search_similar_images(input: ImageSearchInput) -> ImageSearchResult:
    """
    Cloud Vision Web Detection で類似画像を検索する。

    Args:
        input: GCS URI を含む入力

    Returns:
        検索結果の JSON
    """
    from google.cloud import vision

    activity.logger.info(f"画像検索開始: {input.gcs_uri}")

    credentials = _get_vision_credentials()
    if credentials:
        client = vision.ImageAnnotatorClient(credentials=credentials)
    else:
        client = vision.ImageAnnotatorClient()

    image = vision.Image(source=vision.ImageSource(gcs_image_uri=input.gcs_uri))
    response = client.web_detection(image=image)
    web = response.web_detection

    results = {
        "pages": [],
        "full_matches": [],
        "partial_matches": [],
        "visually_similar": [],
    }

    if web.pages_with_matching_images:
        for page in web.pages_with_matching_images:
            page_info = {"url": page.url, "page_title": page.page_title or ""}
            if page.full_matching_images:
                page_info["image_urls"] = [img.url for img in page.full_matching_images]
            elif page.partial_matching_images:
                page_info["image_urls"] = [img.url for img in page.partial_matching_images]
            results["pages"].append(page_info)

    if web.full_matching_images:
        results["full_matches"] = [img.url for img in web.full_matching_images]

    if web.partial_matching_images:
        results["partial_matches"] = [img.url for img in web.partial_matching_images]

    if web.visually_similar_images:
        results["visually_similar"] = [img.url for img in web.visually_similar_images]

    total = (
        len(results["pages"])
        + len(results["full_matches"])
        + len(results["partial_matches"])
        + len(results["visually_similar"])
    )
    activity.logger.info(f"画像検索完了: {total} 件の結果")

    return ImageSearchResult(
        results_json=json.dumps(results, ensure_ascii=False)
    )
