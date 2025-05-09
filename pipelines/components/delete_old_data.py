from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def delete_old_data(events_table: str, aggregation_table: str, project_name: str):
    from datetime import datetime, timedelta
    from google.cloud import bigquery

    # 365 days ago
    one_year_ago = (datetime.now() - timedelta(days=365)).timestamp()

    def delete_old_data_from_events_table():
        return f"""
                DELETE FROM `{events_table}`
                WHERE currentMeasurement.stats_timestamp < "{one_year_ago}"
        """

    def delete_old_data_from_aggregation_table():
        return f"""
                DELETE FROM `{aggregation_table}`
                WHERE stats_timestamp < "{one_year_ago}"
        """

    bigquery_client = bigquery.Client(project=project_name)

    print(f"BigQuery: start deleting rows older than 365 days from {events_table}")
    query = delete_old_data_from_events_table()
    # Start the query
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Deleted {result.total_rows} rows from {events_table}")

    print(f"BigQuery: start deleting rows older than 365 days from {aggregation_table}")
    query = delete_old_data_from_aggregation_table()
    # Start the query
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Deleted {result.total_rows} rows from {aggregation_table}")
