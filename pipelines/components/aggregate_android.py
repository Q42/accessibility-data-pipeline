from kfp.v2.dsl import component


@component(packages_to_install=["google-cloud-bigquery==2.22.0", "pytz"])
def bigquery_aggregate_events_op(
    updates_table: str, aggregation_table: str, project_name: str
) -> str:
    from google.cloud import bigquery

    def aggregate_events_query(select_statement: str):
        return f"""
                INSERT INTO `{aggregation_table}`
                SELECT {select_statement} FROM `{updates_table}`;
                DELETE FROM `{aggregation_table}`
                WHERE (CONCAT(fields_hash, stats_timestamp) 
                IN (SELECT CONCAT(previous_hash, previousMeasurement.stats_timestamp) concatenated_updates 
                FROM `{updates_table}`))
        """

    # dynamically build the select statement to appropriately follow any updates in the schema
    def get_aggregate_select_statement():
        project = aggregation_table.split(".")[1]
        table = aggregation_table.split(".")[2]
        table_ref = bigquery.DatasetReference(project_name, project).table(table)
        struct_schema = bigquery_client.get_table(table_ref).schema
        select_statement = []
        for field in struct_schema:
            if field.name in ["screen_display_scale_default_comparison", "screen_font_scale_default_comparison"]:
                select_statement.append("NULL")
            elif field.name == "fields_hash":
                select_statement.append("current_hash as fields_hash")
            else:
                select_statement.append(f"currentMeasurement.{field.name}")
        print(", ".join(select_statement))
        return ", ".join(select_statement)

    print(f"BigQuery: start aggregating event data")
    bigquery_client = bigquery.Client(project=project_name)

    aggregate_select_statement = get_aggregate_select_statement()

    query = aggregate_events_query(aggregate_select_statement)

    # Start the query
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Aggregate finished: {result.total_rows}")
    return aggregation_table
