"""
GCS 接続テスト — Base64 キーの検証とアップロード確認
"""
import base64
import json
import os
import sys
import tempfile

from dotenv import load_dotenv
load_dotenv()


def test_gcs_key():
    key_b64 = os.getenv("GCS_SA_KEY_BASE64", "")
    if not key_b64:
        print("ERROR: GCS_SA_KEY_BASE64 が未設定です")
        sys.exit(1)

    print(f"Base64 文字列長: {len(key_b64)}")

    # Base64 デコード
    try:
        decoded = base64.b64decode(key_b64)
        print(f"デコード後バイト数: {len(decoded)}")
    except Exception as e:
        print(f"ERROR: Base64 デコード失敗: {e}")
        sys.exit(1)

    # JSON パース
    try:
        info = json.loads(decoded.decode("utf-8"))
        print(f"JSON パース成功: type={info.get('type')}, project_id={info.get('project_id')}")
        print(f"  private_key_id: {info.get('private_key_id')}")
        print(f"  client_email:   {info.get('client_email')}")
    except Exception as e:
        print(f"ERROR: JSON パース失敗: {e}")
        print(f"  デコードされたデータ（先頭200バイト）: {decoded[:200]}")
        sys.exit(1)

    # GCS クライアント作成
    try:
        from google.cloud import storage
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_info(info)
        client = storage.Client(credentials=credentials, project=credentials.project_id)
        print(f"GCS クライアント作成成功: project={credentials.project_id}")
    except Exception as e:
        print(f"ERROR: GCS クライアント作成失敗: {e}")
        sys.exit(1)

    # バケット確認
    bucket_name = os.getenv("GCS_BUCKET_NAME", "")
    if not bucket_name:
        print("WARNING: GCS_BUCKET_NAME が未設定のためアップロードテストをスキップ")
        sys.exit(0)

    # テストファイルアップロード
    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob("test/connection_check.txt")
        blob.upload_from_string(b"GCS connection test OK", content_type="text/plain")
        print(f"アップロード成功: gs://{bucket_name}/test/connection_check.txt")
    except Exception as e:
        print(f"ERROR: アップロード失敗: {e}")
        sys.exit(1)

    print("\n全テスト通過")


if __name__ == "__main__":
    test_gcs_key()
