import sys
from models.A11yDashboard import A11yDashboard
from models.Config import Config

scope = sys.argv[1]
base_config = Config(scope)
bigquery_client = base_config.client
google_project = base_config.project_name
config = base_config.config
pipeline_version = base_config.pipeline_version
organisation = config["label"]


for operating_system in ["ios", "android"]:
    # gather the latest aggregation results to determine the relevant properties
    query = f"""
    WITH
        ds AS (SELECT * FROM `{google_project}.aggregations.pipeline_{organisation}_{operating_system}_{pipeline_version}`)
            SELECT * FROM ds WHERE date = (select max(date) from ds) LIMIT 100"""
    # Start the query, passing in the extra configuration and wait for result
    query_job = bigquery_client.query(query)
    result = query_job.result()
    # print(result.pages)
    properties = [dict(row) for page in result.pages for row in page]
    # print(properties)

a = A11yDashboard("test", ["test"], "test_src", "ios", "hema")
print([obj for obj in a.properties["screen_font_scale_default_comparison"]])
# print(a.properties)
