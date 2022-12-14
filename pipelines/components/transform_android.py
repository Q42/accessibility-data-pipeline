from kfp.v2.dsl import component


@component(packages_to_install=["google-cloud-bigquery==2.22.0", "pytz"])
def bigquery_raw_data_to_typed_data_op(raw_data_table: str, updates_table: str, events_table: str,
                                       project_name: str) -> str:
    from google.cloud import bigquery

    def transform_raw_data_to_typed_data_query():
        android_fields = [
            # Regular fields
            {"name": "stats_timestamp", "from_name": "Stats_timestamp"},
            {"name": "stats_version", "from_name": "Stats_Model_Version"},
            {"name": "app_bundle_identifier", "from_name": "applicationId"},
            # Fields w.r.t. system
            {"name": "system_sdk_version", "from_name": "sdkVersion"},
            {"name": "system_default_language", "from_name": "defaultLanguage"},
            {"name": "manufacturer", "from_name": "manufacturer"},
            {"name": "model_name", "from_name": "modelName"},
            # Fields w.r.t. preference
            {"name": "preference_daytime", "from_name": "daytime"},
            {"name": "preference_is_nightmode_enabled", "from_name": "isNightmodeEnabled", "type": "BOOLEAN"},
            # Fields w.r.t. screen
            {"name": "screen_orientation", "from_name": "screenOrientation"},
            {"name": "screen_display_scale", "from_name": "displayScale"},
            {"name": "screen_font_scale", "from_name": "fontScale"},
            # Fields w.r.t. accessibility
            {"name": "accessibility_enabled_accessibility_services", "from_name": "enabledAccessibilityServices",
             "mode": "REPEATED"},
            {"name": "accessibility_is_accessibility_manager_enabled", "from_name": "isAccessibilityManagerEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_closed_captioning_enabled", "from_name": "isClosedCaptioningEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_touch_exploration_enabled", "from_name": "isTouchExplorationEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_voice_access_enabled", "from_name": "isVoiceAccessEnabled", "type": "BOOLEAN"},
            {"name": "accessibility_is_talk_back_enabled", "from_name": "isTalkBackEnabled", "type": "BOOLEAN"},
            {"name": "accessibility_is_samsung_talk_back_enabled", "from_name": "isSamsungTalkbackEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_select_to_speak_enabled", "from_name": "isSelectToSpeakEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_braille_back_enabled", "from_name": "isBrailleBackEnabled", "type": "BOOLEAN"},
            {"name": "accessibility_is_color_blind_mode_enabled", "from_name": "isColorBlindModeEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_color_inversion_enabled", "from_name": "isColorInversionEnabled",
             "type": "BOOLEAN"},
            {"name": "accessibility_is_switch_access_enabled", "from_name": "isSwitchAccessEnabled", "type": "BOOLEAN"},
        ]

        # Fixes for legacy field names and data types
        def map_field(field, version):
            from_name = field['from_name'] if 'from_name' in field else field['name']
            if "type" in field:
                return f"CAST(ds.{version}Measurement.`{from_name}` AS {field['type']}) AS {field['name']}"
            elif "mode" in field:
                return f"SPLIT(SUBSTR(ds.{version}Measurement.`{from_name}`, 2, LENGTH(ds.{version}Measurement.`{from_name}`) - 2), ', ') AS {field['name']}"
            elif "from_name" in field:
                return f"ds.{version}Measurement.`{from_name}` AS {field['name']}"
            else:
                return f"ds.{version}Measurement.{field['name']} "

        current_fields = map(lambda field: map_field(field, 'current'), android_fields)
        current_fields_str = ", ".join(current_fields)

        previous_fields = map(lambda field: map_field(field, 'previous'), android_fields)
        previous_fields_str = ", ".join(previous_fields)

        current_hash_input_fields = [f"CAST(ds.currentMeasurement.`{field['from_name']}` AS STRING)" for field in
                                     android_fields if field['from_name'] != 'Stats_timestamp']
        current_hash_fields = f"{', '.join(current_hash_input_fields)}"

        previous_hash_input_fields = [f"CAST(ds.previousMeasurement.`{field['from_name']}` AS STRING)" for field in
                                      android_fields if field['from_name'] != 'Stats_timestamp']
        previous_hash_fields = f"{', '.join(previous_hash_input_fields)}"
        # Deduplicate, sometimes 2 documents exist with same instance ID and timestamp
        # a check for Stats_Version is to force usage of the fixed version of the  libra
        return f"""
            WITH
                ds AS (SELECT * FROM `{raw_data_table}`),
                events AS (SELECT * FROM `{events_table}`)
            SELECT __key__.name as doc_id,
            STRUCT({current_fields_str}) AS currentMeasurement,
            STRUCT({previous_fields_str}) AS previousMeasurement,
            FARM_FINGERPRINT(array_to_string([{current_hash_fields}], ',')) AS current_hash,
            FARM_FINGERPRINT(array_to_string([{previous_hash_fields}], ',')) AS previous_hash FROM ds WHERE 
            ds.__key__.name NOT IN (select doc_id from events) AND ds.Stats_Version > "Android 2022-07-12" """

    print(f"BigQuery: start transforming raw data to typed data")
    bigquery_client = bigquery.Client(project=project_name)

    # Prepare query job
    job_config = bigquery.QueryJobConfig(destination=updates_table)
    query = transform_raw_data_to_typed_data_query()

    # Start the query, passing in the extra configuration and wait for result
    query_job = bigquery_client.query(query, job_config=job_config)
    result = query_job.result()

    print(f"Transform finished: {result.total_rows}")
    return updates_table
