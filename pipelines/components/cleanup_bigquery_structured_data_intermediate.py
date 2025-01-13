from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def cleanup_bigquery_structured_data_intermediate(structured_data_table: str, project_name: str):
    from google.cloud import bigquery

    print(f"BigQuery: delete structured data intermediate")
    bigquery_client = bigquery.Client(project=project_name)
    bigquery_client.delete_table(structured_data_table)
    print(f"Delete finished")
