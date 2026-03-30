from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def bigquery_add_custom_properties(aggregation_table: str, project_name: str) -> str:
    from google.cloud import bigquery

    def add_custom_properties():
        return f"""
                UPDATE `{aggregation_table}` aggregated SET screen_display_scale_default_comparison = CASE
                WHEN aggregated.screen_display_scale < defaults.screen_display_scale THEN 'smaller'
                WHEN aggregated.screen_display_scale > defaults.screen_display_scale THEN 'bigger'
                ELSE 'default'
                END
                FROM `{project_name}.property_transformations.screen_display_scale_defaults` defaults
                WHERE aggregated.manufacturer = defaults.manufacturer and aggregated.model_name = defaults.model_name;
                UPDATE `{aggregation_table}` aggregated SET screen_font_scale_default_comparison = CASE
                WHEN aggregated.screen_font_scale < defaults.screen_font_scale THEN 'smaller'
                WHEN aggregated.screen_font_scale > defaults.screen_font_scale THEN 'bigger'
                ELSE 'default'
                END
                FROM `{project_name}.property_transformations.screen_font_scale_defaults` defaults
                WHERE aggregated.manufacturer = defaults.manufacturer and aggregated.model_name = defaults.model_name;
        """

    print(f"BigQuery: start adding custom properties to aggregated data")
    bigquery_client = bigquery.Client(project=project_name)

    query = add_custom_properties()

    # Start the query
    query_job = bigquery_client.query(query)
    result = query_job.result()

    print(f"Added custom properties for: {result.total_rows} rows")
    return aggregation_table
