from kfp.v2.dsl import component

@component(packages_to_install=["google-cloud-bigquery==2.22.0", "pytz"])
def cleanup_bigquery_raw_data_intermediate(raw_data_table: str, project_name: str):
    from google.cloud import bigquery

    print(f"BigQuery: delete raw data intermediate")
    bigquery_client = bigquery.Client(project=project_name)
    bigquery_client.delete_table(raw_data_table)
    print(f"Delete finished")
