from pathlib import Path
from typing import Iterable
import boto3, os

def upload_files(bucket: str, files: Iterable[Path], prefix: str = "") -> None:
    """
    Upload *files* (Path objects) to S3 *bucket* under key prefix *prefix*.
    """
    s3 = boto3.client("s3")
    for f in files:
        key = f"{prefix.rstrip('/')}/{f.name}" if prefix else f.name
        s3.upload_file(str(f), bucket, key)
        print(f"Uploaded {f} → s3://{bucket}/{key}")