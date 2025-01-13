# Vertex AI Pipeline
Pipelines to move data from Firestore to Bigquery.

## Prerequisites
- Python 3.9

## Setup
- Create virtualenv: `pyenv virtualenv accessibility-pipeline`
- Activate virtualenv: `pyenv activate accessibility-pipeline`
- Install deps: `pip install -r requirements.txt`

## Run
- Fetch config files from 1PW Vault `Team a11y` and copy to folder `config/`
- Kick-off single run: `python deploy_single_run.py <android|ios> <project>`

## Deploy
- Deploy as cron: `python deploy_cron.py <android|ios>`
  - Note: this will replace the Kubeflow template in GCS, so the new template will be used in the next tick of the Cloud Scheduler
  - Note: if you want to export data for a new client, you need to create a new Cloud Scheduler by hand

## Run CLI
- Create an `organisations.json` file in this directory containing the following schema:
```
{
  "organisations": ["example_org_1", "example_org_2"]
}
```
- Run the CLI using `python main.py`
