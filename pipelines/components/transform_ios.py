from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def bigquery_raw_data_to_typed_data_op(raw_data_table: str, updates_table: str, events_table: str,
                                       project_name: str) -> str:
    from google.cloud import bigquery
    iOS_fields = [
                # Regular fields
                {"name": "stats_timestamp", "from_name": "Stats_timestamp"},
                {"name": "stats_version", "from_name": "Stats_version"},
                {"name": "app_bundle_identifier", "from_name": "App_bundle_identifier"},
                # Fields w.r.t. system
                {"name": "system_model_id", "from_name": "System_model_id"},
                {"name": "system_model_name", "from_name": "System_model_name"},
                {"name": "system_os_major_version", "from_name": "System_OS_major_version"},
                {"name": "system_preferred_language", "from_name": "System_Preferred_language"},
                {"name": "system_dutch_region", "from_name": "System_Dutch_region", "type": "BOOLEAN"},
                # Fields w.r.t. preference
                {"name": "preference_ui_style", "from_name": "Preference_UI_style"},
                {"name": "preference_preferred_content_size", "from_name": "Preference_preferred_content_size"},
                {"name": "preference_daytime", "from_name": "Preference_daytime"},
                # Fields w.r.t. screen
                {"name": "screen_width", "from_name": "Screen_width", "type": "INTEGER"},
                {"name": "screen_window_width", "from_name": "Screen_window_width", "type": "INTEGER"},
                {"name": "screen_scale", "from_name": "Screen_scale"},
                {"name": "screen_zoomed", "from_name": "Screen_zoomed", "type": "BOOLEAN"},
                {"name": "screen_orientation", "from_name": "Screen_orientation"},
                {"name": "screen_display_gamut", "from_name": "Screen_display_gamut"},
                {"name": "screen_device_idiom", "from_name": "Screen_device_idiom"},
                {"name": "screen_in_split_screen", "from_name": "Screen_in_split_screen", "type": "BOOLEAN"},
                # Fields w.r.t. accessibility
                {"name": "accessibility_uses_any_accessibility_setting",
                "from_name": "Accessibility_uses_any_accessibility_setting", "type": "BOOLEAN"},
                {"name": "accessibility_is_switch_control_running", "from_name": "Accessibility_isSwitchControlRunning",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_voice_over_running", "from_name": "Accessibility_isVoiceOverRunning",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_invert_colors_enabled", "from_name": "Accessibility_isInvertColorsEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_assistive_touch_running_with_is_guided_access_enabled",
                "from_name": "Accessibility_isAssistiveTouchRunning_with_isGuidedAccessEnabled"},
                {"name": "accessibility_is_speak_screen_enabled", "from_name": "Accessibility_isSpeakScreenEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_mono_audio_enabled", "from_name": "Accessibility_isMonoAudioEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_guided_access_enabled", "from_name": "Accessibility_isGuidedAccessEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_darker_system_colors_enabled",
                "from_name": "Accessibility_isDarkerSystemColorsEnabled", "type": "BOOLEAN"},
                {"name": "accessibility_is_closed_captioning_enabled",
                "from_name": "Accessibility_isClosedCaptioningEnabled", "type": "BOOLEAN"},
                {"name": "accessibility_is_reduce_transparency_enabled",
                "from_name": "Accessibility_isReduceTransparencyEnabled", "type": "BOOLEAN"},
                {"name": "accessibility_is_shake_to_undo_enabled", "from_name": "Accessibility_isShakeToUndoEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_bold_text_enabled", "from_name": "Accessibility_isBoldTextEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_grayscale_enabled", "from_name": "Accessibility_isGrayscaleEnabled",
                "type": "BOOLEAN"},
                {"name": "accessibility_is_speak_selection_enabled", "from_name": "Accessibility_isSpeakSelectionEnabled",
                "type": "BOOLEAN"},
                # Fields w.r.t. Apple Pay
                {"name": "apple_pay_available", "from_name": "Apple_Pay_available", "type": "BOOLEAN"},
                {"name": "apple_pay_with_maestro_available", "from_name": "Apple_Pay_with_Maestro_available",
                "type": "BOOLEAN"},
                # Fields w.r.t. Apple Watch
                {"name": "watch_paired", "from_name": "Watch_paired", "type": "BOOLEAN"},
                {"name": "watch_supported", "from_name": "Watch_supported", "type": "BOOLEAN"},
            ]

    # Update the schema of the raw data table to always include previousMeasurement and the required struct fields
    def update_table_schema(table_ref):
        table = bigquery_client.get_table(table_ref)
        current_schema = table.schema
        struct_fields_schemas = {bigquery.SchemaField(field["from_name"], 'STRING', mode='NULLABLE') for field in iOS_fields}
        key_field = bigquery.SchemaField("__key__", 'RECORD', mode='NULLABLE', fields=[
            bigquery.SchemaField('namespace', 'STRING', mode='NULLABLE'),
            bigquery.SchemaField('app', 'STRING', mode='NULLABLE'),
            bigquery.SchemaField('path', 'STRING', mode='NULLABLE'),
            bigquery.SchemaField('kind', 'STRING', mode='NULLABLE'),
            bigquery.SchemaField('name', 'STRING', mode='NULLABLE'),
            bigquery.SchemaField('id', 'INTEGER', mode='NULLABLE'),
            ])

        struct_fields_schemas.add(key_field)

        new_schema = []
        for field in current_schema:
            if field.field_type == 'RECORD' and field.name in ['currentMeasurement', 'previousMeasurement']:
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
        bigquery_client.update_table(table, ['schema'])
        print(f"Schema updated for table {table_ref}")

    def transform_raw_data_to_typed_data_query():
        # Fixes for legacy field names and data types
        def map_field(field, version):
            from_name = field['from_name'] if 'from_name' in field else field['name']
            if "type" in field:
                return f"CAST(ds.{version}Measurement.{from_name} AS {field['type']}) AS {field['name']}"
            elif "mode" in field:
                return f"SPLIT(SUBSTR(ds.{version}Measurement.{from_name}, 2, LENGTH(ds.{version}Measurement.{from_name}) - 2), ', ') AS {field['name']}"
            elif "from_name" in field:
                return f"ds.{version}Measurement.{from_name} AS {field['name']}"
            else:
                return f"ds.{version}Measurement.{field['name']}"

        current_fields = map(lambda field: map_field(field, 'current'), iOS_fields)
        current_fields_str = ", ".join(current_fields)

        previous_fields = map(lambda field: map_field(field, 'previous'), iOS_fields)
        previous_fields_str = ", ".join(previous_fields)

        current_hash_input_fields = [f"CAST(ds.currentMeasurement.{field['from_name']} AS STRING)" for field in
                                     iOS_fields if field['from_name'] != 'Stats_timestamp']
        current_hash_fields = f"{', '.join(current_hash_input_fields)}"

        previous_hash_input_fields = [f"CAST(ds.previousMeasurement.{field['from_name']} AS STRING)" for field in
                                      iOS_fields if field['from_name'] != 'Stats_timestamp']
        previous_hash_fields = f"{', '.join(previous_hash_input_fields)}"
        return f"""
            WITH
                ds AS (SELECT * FROM `{raw_data_table}`),
                events AS (SELECT * FROM `{events_table}`)
            SELECT __key__.name AS doc_id,
            STRUCT({current_fields_str}) AS currentMeasurement,
            STRUCT({previous_fields_str}) AS previousMeasurement,
            FARM_FINGERPRINT(array_to_string([{current_hash_fields}], ',')) AS current_hash,
            FARM_FINGERPRINT(array_to_string([{previous_hash_fields}], ',')) AS previous_hash
            FROM ds
            WHERE ds.__key__.name NOT IN (select doc_id from events)
        """

    print(f"BigQuery: start transforming raw data to typed data")
    bigquery_client = bigquery.Client(project=project_name)

    # Update schema
    raw_data_table_ref = bigquery.TableReference.from_string(raw_data_table, default_project=project_name)
    update_table_schema(raw_data_table_ref)

    # 2. Prepare query for transformation job
    job_config = bigquery.QueryJobConfig(destination=updates_table)
    query = transform_raw_data_to_typed_data_query()

    # 3. Start the query, passing in the extra configuration and wait for result
    query_job = bigquery_client.query(query, job_config=job_config)
    result = query_job.result()

    print(f"Transform finished: {result.total_rows}")
    return updates_table
