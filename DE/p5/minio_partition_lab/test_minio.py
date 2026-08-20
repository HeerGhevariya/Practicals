import boto3

s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="admin",
    aws_secret_access_key="Minio@12345"
)

response = s3.list_buckets()

print("Connected to MinIO successfully!")

print("Buckets:")

for bucket in response["Buckets"]:
    print("-", bucket["Name"])