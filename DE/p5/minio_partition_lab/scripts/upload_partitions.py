import boto3
import os

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="Minio@12345"
)

BUCKET = "metrics"

BASE_DIR = "../data/partitions"

for root, dirs, files in os.walk(BASE_DIR):

    for file in files:

        local_path = os.path.join(root, file)

        relative_path = os.path.relpath(
            local_path,
            BASE_DIR
        )

        object_key = relative_path.replace("\\", "/")

        print("Uploading:", object_key)

        s3.upload_file(
            local_path,
            BUCKET,
            object_key
        )

print()
print("All partitions uploaded successfully!")