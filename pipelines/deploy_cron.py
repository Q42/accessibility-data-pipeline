import sys
import json
from args import get_platform_from_args
from compile import compile_pipeline
from google.cloud import storage

platform = get_platform_from_args(sys.argv)

# Compile
job_spec_path = compile_pipeline(platform)

# load universal pipeline settings
with open("../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# Google Cloud project name
project_name = settings["project_name"]
storage_bucket = settings["storage_bucket"]

# Upload to GCS
storage_client = storage.Client(project=project_name)
bucket = storage_client.bucket(storage_bucket)

blob = bucket.blob(f"schemas/schema-{platform}.json")
blob.upload_from_filename(f"schemas/schema-{platform}.json")

blob = bucket.blob(f"templates/{job_spec_path}")
blob.upload_from_filename(job_spec_path)

print(f"Uploaded {job_spec_path} to GCS")
