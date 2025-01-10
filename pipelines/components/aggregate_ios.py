from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def bigquery_aggregate_events_op(updates_table: str, aggregation_table: str, project_name: str) -> str:
    from google.cloud import bigquery

    def aggregate_events_query():
        return f"""
                INSERT INTO `{aggregation_table}`
                SELECT currentMeasurement.*, current_hash as fields_hash FROM `{updates_table}`;
                DELETE FROM `{aggregation_table}`
                WHERE (CONCAT(fields_hash, stats_timestamp) IN (SELECT CONCAT(previous_hash, previousMeasurement.stats_timestamp) concatenated_updates FROM `{updates_table}`))
        """

    print(f"BigQuery: start aggregating event data")
    bigquery_client = bigquery.Client(project=project_name)

    query = aggregate_events_query()

    # Start the query
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Aggregate finished: {result.total_rows}")
    return aggregation_table
