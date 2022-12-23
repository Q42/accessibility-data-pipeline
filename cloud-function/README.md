# Cloud Function
Function is triggerd by Cloud Scheduler and executes a Vertex AI Pipeline.

## Prerequisites
- Python 3.9
- GCloud SDK

## Setup
- Create virtualenv: `pyenv virtualenv accessibility-pipeline`
- Activate virtualenv: `pyenv activate accessibility-pipeline`
- Install deps: `pip install -r requirements.txt`

## Deploy
- `gcloud functions deploy pipeline-executor --entry-point process_request --runtime python39 --trigger-http --region europe-west2 --project {project_name}`
