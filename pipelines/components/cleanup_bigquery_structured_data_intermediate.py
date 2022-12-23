from kfp.v2.dsl import component

@component(packages_to_install=["google-cloud-bigquery==2.22.0", "pytz"])
def cleanup_bigquery_structured_data_intermediate(structured_data_table: str, project_name: str):
    from google.cloud import bigquery

    print(f"BigQuery: delete structured data intermediate")
    bigquery_client = bigquery.Client(project=project_name)
    bigquery_client.delete_table(structured_data_table)
    print(f"Delete finished")
