from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def bigquery_import_op(collection_id: str, table_id: str, storage_uri_prefix: str, project_name: str) -> str:
    from google.cloud import bigquery

    print(f"BigQuery: starting import")
    bigquery_client = bigquery.Client(project=project_name)

    # Prepare import job
    job_config = bigquery.LoadJobConfig(source_format='DATASTORE_BACKUP')
    uri = f"{storage_uri_prefix}/all_namespaces/kind_{collection_id}/all_namespaces_kind_{collection_id}.export_metadata"

    # Create table
    table = bigquery_client.create_table(table_id)

    # Start import and wait for result
    job = bigquery_client.load_table_from_uri(
        uri,
        table,
        location="europe-west4",
        job_config=job_config
    )
    result = job.result()

    print(f"Import finished. Imported {result.output_rows} row to {result.destination}")
    return str(result.destination)
