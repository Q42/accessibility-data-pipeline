import json
import time
from datetime import date
from google.cloud import aiplatform

# load universal pipeline settings
with open("../../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# Google Cloud project name
project_name = settings["project_name"]
storage_bucket = settings["storage_bucket"]

PROJECT_ID = project_name
REGION = 'europe-west2'
PIPELINE_ROOT = f'gs://{storage_bucket}/artifacts'


def process_request(request):
    """Processes the incoming HTTP request.

   Args:
     request (flask.Request): HTTP request object.

   Returns:
     The response text or any set of values that can be turned into a Response
     object using `make_response
     <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
   """
    day = date.today().strftime("%Y-%m-%d")
    current_epoch = int(time.time())
    pipeline_job_version = f"{day}-{current_epoch}"
    print(f"Pipeline job version: {pipeline_job_version}")

    # decode http request payload and translate into JSON object
    request_str = request.data.decode('utf-8')
    request_json = json.loads(request_str)

    pipeline_spec_uri = request_json['pipeline_spec_uri']
    parameter_values = request_json['parameter_values']
    parameter_values.update({"pipeline_job_version": pipeline_job_version})

    pipeline_job_id = request_json["pipeline_run"]

    aiplatform.init(
        project=PROJECT_ID,
        location=REGION,
    )

    job = aiplatform.PipelineJob(
        display_name='Export Firestore to BigQuery (cron)',
        template_path=pipeline_spec_uri,
        pipeline_root=PIPELINE_ROOT,
        enable_caching=False,
        parameter_values=parameter_values,
        job_id=f"{pipeline_job_id}-{pipeline_job_version}"
    )

    job.submit()
    return "Job submitted"
