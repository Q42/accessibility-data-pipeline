from google.cloud import bigquery

from .schema import SchemaField

def recompute_event_hashes_query(table_to_recompute: str, typed_schema: list[SchemaField]):
    current_hash_input_fields = [f"CAST(currentMeasurement.`{field.name}` AS STRING)" if field.mode != "REPEATED" else f"ARRAY_TO_STRING(currentMeasurement.`{field.name}`, ', ')" for field in typed_schema]
    current_hash_fields = ", ".join(current_hash_input_fields)

    previous_hash_input_fields = [f"CAST(previousMeasurement.`{field.name}` AS STRING)" if field.mode != "REPEATED" else f"ARRAY_TO_STRING(previousMeasurement.`{field.name}`, ', ')" for field in typed_schema]
    previous_hash_fields = ", ".join(previous_hash_input_fields)


    query = f"""
    UPDATE {table_to_recompute}
    SET current_hash = FARM_FINGERPRINT(array_to_string([{current_hash_fields}], ',')),
        previous_hash = FARM_FINGERPRINT(array_to_string([{previous_hash_fields}], ','))
    WHERE TRUE;
    """

    return query

def recompute_aggregated_hashes_query(table_to_recompute: str, typed_schema: list[SchemaField]):
    hash_input_fields = [f"CAST(`{field.name}` AS STRING)" if field.mode != "REPEATED" else f"ARRAY_TO_STRING(`{field.name}`, ', ')" for field in typed_schema]
    hash_fields = ", ".join(hash_input_fields)

    query = f"""
    UPDATE {table_to_recompute}
    SET fields_hash = FARM_FINGERPRINT(array_to_string([{hash_fields}], ','))
    WHERE TRUE;
    """

    return query

def recompute_hashes(platform: str, organisation: str, project_name: str, pipeline_version: str, typed_schema: list[SchemaField]):
    bigquery_client = bigquery.Client(project=project_name)

    aggregated_table = f"pipeline_{organisation}.danny_aggregated_data_{platform}_{pipeline_version}"
    event_table = f"pipeline_{organisation}.danny_event_data_{platform}_{pipeline_version}"


    print(f"Recomputing hashes for: {aggregated_table}...")
    query = recompute_aggregated_hashes_query(aggregated_table, typed_schema)
    print(query)
    # Start the query
    query_job = bigquery_client.query(query)
    query_job.result() # Wait for the job to finish

    print(f"- Recomputed hashes for {query_job.num_dml_affected_rows} rows\n")


    print(f"Recomputing hashes for: {event_table}...")
    query = recompute_event_hashes_query(event_table, typed_schema)
    # Start the query
    query_job = bigquery_client.query(query)
    query_job.result() # Wait for the job to finish

    print(f"- Recomputed hashes for {query_job.num_dml_affected_rows} rows\n")
