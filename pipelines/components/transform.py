from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0", "google-cloud-storage==2.19.0"],
    base_image="python:3.13"
)
def bigquery_raw_data_to_typed_data_op(raw_data_table: str, updates_table: str, events_table: str,
                                       project_name: str, platform: str, storage_bucket: str) -> str:
    from google.cloud import bigquery, storage
    from dataclasses import dataclass
    import json

    @dataclass
    class SchemaField:
        raw_name: str
        name: str
        type: str = "STRING"
        mode: str = None

    # Retrieve the schema for the current platform from the storage bucket
    storage_client = storage.Client(project=project_name)
    bucket = storage_client.bucket(storage_bucket)
    blob = bucket.blob(f"schemas/schema-{platform}.json")
    schema = json.loads(blob.download_as_string())

    typed_schema: list[SchemaField] = []

    for field in schema:
        typed_schema.append(SchemaField(
            # The firestore name may contain spaces whereas the BigQuery name cannot
            raw_name=str(field["event_name"]).replace(" ", "_"),
            name=field["name"],
            type=field["type"] if "type" in field else "STRING",
            mode=field["mode"] if "mode" in field else None,
        ))

    # Update the schema of the raw data table to always include previousMeasurement and the required struct fields
    def update_table_schema(table_ref):
        table = bigquery_client.get_table(table_ref)
        current_schema = table.schema
        struct_fields_schemas = {bigquery.SchemaField(field.raw_name, "STRING", mode="NULLABLE") for field in typed_schema}
        key_field = bigquery.SchemaField("__key__", "RECORD", mode="NULLABLE", fields=[
            bigquery.SchemaField("namespace", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("app", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("path", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("kind", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("name", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("id", "INTEGER", mode="NULLABLE"),
        ])

        struct_fields_schemas.add(key_field)

        new_schema: list[bigquery.SchemaField] = []
        for field in current_schema:
            if field.field_type == "RECORD" and field.name in ["currentMeasurement", "previousMeasurement"]:
                new_struct_field = bigquery.SchemaField(
                    name=field.name,
                    field_type=field.field_type,
                    mode=field.mode,
                    fields=struct_fields_schemas
                )
                new_schema.append(new_struct_field)
            else:
                new_schema.append(field)

        if "previousMeasurement" not in [field.name for field in new_schema]:
            new_schema.append(bigquery.SchemaField("previousMeasurement", "RECORD", mode="NULLABLE", fields=struct_fields_schemas))

        table.schema = new_schema
        bigquery_client.update_table(table, ["schema"])
        print(f"Schema updated for table {table_ref}")

    def transform_raw_data_to_typed_data_query():
        def map_field(field: SchemaField, version: str) -> str:
            # If the field is a repeated field, we need to split the string into an array
            # The array is a string in the form of [value1, value2, value3]
            # - SUBSTR is used to remove the brackets
            # - SPLIT is used to convert the string into an array
            # We always assume the array is an array of strings
            if field.mode == "REPEATED":
                return f"SPLIT(SUBSTR(ds.{version}Measurement.`{field.raw_name}`, 2, LENGTH(ds.{version}Measurement.`{field.raw_name}`) - 2), ', ') AS {field.name}"

            # Otherwise we cast the field to the correct type
            return f"CAST(ds.{version}Measurement.`{field.raw_name}` AS {field.type}) AS {field.name}"

        current_fields = map(lambda field: map_field(field, "current"), typed_schema)
        current_fields_str = ", ".join(current_fields)

        previous_fields = map(lambda field: map_field(field, "previous"), typed_schema)
        previous_fields_str = ", ".join(previous_fields)

        current_hash_input_fields = [f"CAST(ds.currentMeasurement.`{field.raw_name}` AS STRING)" for field in typed_schema]
        current_hash_fields = f"{', '.join(current_hash_input_fields)}"

        previous_hash_input_fields = [f"CAST(ds.previousMeasurement.`{field.raw_name}` AS STRING)" for field in typed_schema]
        previous_hash_fields = f"{', '.join(previous_hash_input_fields)}"

        # A check for Stats_Version is to force usage of the fixed version of the library
        and_statement = ""

        if platform == "android":
            and_statement = "AND ds.currentMeasurement.Stats_Version > 'Android 2022-07-12'"

        # Deduplicate, sometimes 2 documents exist with same instance ID and timestamp
        return f"""
            WITH
                ds AS (SELECT * FROM `{raw_data_table}`),
                events AS (SELECT * FROM `{events_table}`)
            SELECT __key__.name as doc_id,
            STRUCT({current_fields_str}) AS currentMeasurement,
            STRUCT({previous_fields_str}) AS previousMeasurement,
            FARM_FINGERPRINT(array_to_string([{current_hash_fields}], ',')) AS current_hash,
            FARM_FINGERPRINT(array_to_string([{previous_hash_fields}], ',')) AS previous_hash
            FROM ds
            WHERE ds.__key__.name NOT IN (SELECT doc_id FROM events)
            {and_statement};
            """

    print(f"BigQuery: start transforming raw data to typed data")
    bigquery_client = bigquery.Client(project=project_name)

    # Update schema
    raw_data_table_ref = bigquery.TableReference.from_string(raw_data_table, default_project=project_name)
    update_table_schema(raw_data_table_ref)

    # Prepare query job
    job_config = bigquery.QueryJobConfig(
        destination=updates_table,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )
    query = transform_raw_data_to_typed_data_query()

    # Start the query, passing in the extra configuration and wait for result
    query_job = bigquery_client.query(query, job_config=job_config)
    result = query_job.result()

    print(query)

    print(f"Transform finished: {result.total_rows}")
    return updates_table
