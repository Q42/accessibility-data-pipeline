from kfp.dsl import component


@component(
    packages_to_install=["google-cloud-bigquery==3.40.1"],
    base_image="python:3.14"
)
def cleanup_bigquery_raw_data_intermediate(raw_data_table: str, project_name: str):
    from google.cloud import bigquery

    print(f"BigQuery: delete raw data intermediate")
    bigquery_client = bigquery.Client(project=project_name)
    bigquery_client.delete_table(raw_data_table)
    print(f"Delete finished")
