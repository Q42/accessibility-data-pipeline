import sys
import time
import json
from datetime import date
import google.cloud.aiplatform as aip
from google.cloud import storage
from args import get_platform_from_args
from args import get_project_from_args
from compile import compile_pipeline

# Parse cmdline args
platform = get_platform_from_args(sys.argv)
project = get_project_from_args(sys.argv)

# load universal pipeline settings
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# pipeline version
pipeline_version = config["pipeline_version"]

# Compile pipeline
job_spec_path = compile_pipeline(platform)

# Define pipeline version
day = date.today().strftime("%Y-%m-%d")
current_epoch = int(time.time())
pipeline_job_version = f"{day}-{current_epoch}"

# load universal pipeline settings
with open("../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# Google Cloud project name
project_name = settings["project_name"]
storage_bucket = settings["storage_bucket"]


# Get parameter values
def parameter_values(platform):
    with open(f"config/{platform}-{project}.json", 'r') as f:
        data = json.load(f)
        data["pipeline_job_version"] = pipeline_job_version
        return data

# Upload schema to GCS
storage_client = storage.Client(project=project_name)
bucket = storage_client.bucket(storage_bucket)
blob = bucket.blob(f"schemas/schema-{platform}.json")
blob.upload_from_filename(f"schemas/schema-{platform}.json")

# Create single run
job = aip.PipelineJob(
    display_name=f"Export Firestore to BigQuery {platform}, {parameter_values(platform)['organisation_identifier']}",
    enable_caching=True,
    template_path=job_spec_path,
    parameter_values=parameter_values(platform),
    project=project_name,
    location="europe-west2",
    job_id=f"local-run-{platform}-{project}-{pipeline_version}-{pipeline_job_version}"
)
job.submit()

print(f"Executed single run for {job_spec_path}")
