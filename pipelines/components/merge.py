from kfp.v2.dsl import component

@component(packages_to_install=["google-cloud-bigquery==2.22.0", "pytz"])
def bigquery_merge_updates_into_events_table_op(updates_table: str, events_table: str, project_name: str) -> str:
    from google.cloud import bigquery

    def merge_updates_into_events_table_query():
        return f"""
                INSERT INTO `{events_table}`
                SELECT * FROM `{updates_table}`
        """

    print(f"BigQuery: start merging updates into events table")
    bigquery_client = bigquery.Client(project=project_name)

    # Prepare query job
    query = merge_updates_into_events_table_query()

    # Start the query, passing in the extra configuration and wait for result
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Merge finished: {result.total_rows}")
    return events_table
