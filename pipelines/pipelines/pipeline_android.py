import json
import kfp.dsl as dsl

from components.cleanup_firestore import firestore_cleanup
from components.firestore_export import firestore_export_op
from components.bigquery_import import bigquery_import_op
from components.transform_android import bigquery_raw_data_to_typed_data_op
from components.merge import bigquery_merge_updates_into_events_table_op
from components.cleanup_storage_export_intermediate import cleanup_storage_export_intermediate
from components.cleanup_bigquery_raw_data_intermediate import cleanup_bigquery_raw_data_intermediate
from components.cleanup_bigquery_structured_data_intermediate import \
    cleanup_bigquery_structured_data_intermediate
from components.aggregate_android import bigquery_aggregate_events_op
from components.storage_move_files import storage_move_files_op
from components.add_custom_properties import bigquery_add_custom_properties

"""
    Define pipeline.

    Parameters:
    - firestore_database: Firestore database from which to import the data
    - firestore_collection: Firestore collection from which to import the data
    - export_bucket: Cloud Storage bucket to export the Firestore data to
    - import_table: BigQuery table where data from Firestore is imported to
    - events_table: BigQuery table that contains all events that have previously been imported
    - updates_table: BigQuery table with all new events that are imported in this run
    - aggregation_table: BigQuery table in which only the most recent event per installation is kept
    - pipeline_version: the version to track different pipeline jobs. This is value is auto generated and should not be manually set.
    - organisation_identifier: the identifier that is used to identify a specific mobile app in Firestore
    - service_account: the service account to use to export the data from Firestore; if you want to use the default service account, pass `{}`
    """
# load universal project settings
with open("../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# Google Cloud project name
project_name = settings["project_name"]
storage_bucket = settings["storage_bucket"]

# load universal pipeline settings
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# pipeline version
pipeline_version = config["pipeline_version"]


@dsl.pipeline(
    name='export-firestore-to-bigquery-android',
    description='Export Firestore data to BigQuery (Android)',
    pipeline_root=f"gs://{storage_bucket}/artifacts"
)
def pipeline_android(
        firestore_database: str,
        firestore_collection: str,
        export_bucket: str,
        import_table: str,
        events_table: str,
        updates_table: str,
        aggregation_table: str,
        pipeline_job_version: str,
        organisation_identifier: str,
        service_account: dict
):
    platform = "android"
    import_bucket = storage_bucket

    # versioned tables
    temporary_import_table = f"{import_table}_{pipeline_version}_{pipeline_job_version}"
    temporary_updates_table = f"{updates_table}_{pipeline_version}_{pipeline_job_version}"
    events_table = f"{events_table}_{pipeline_version}"
    aggregation_table = f"{aggregation_table}_{pipeline_version}"

    # raw data set with changes from firestore
    export_result = firestore_export_op(firestore_database, firestore_collection, export_bucket,
                                        organisation_identifier, platform, pipeline_version,
                                        service_account)
    # if needed, move exported data to correct region
    move_result = storage_move_files_op(export_bucket, import_bucket, export_result.output, project_name)
    # transfer changes data set to bigquery
    import_result = bigquery_import_op(firestore_collection, temporary_import_table, move_result.output, project_name)
    # transform bigquery changes table (remove duplicates) and cast correct types
    transform_result = bigquery_raw_data_to_typed_data_op(import_result.output, temporary_updates_table, events_table,
                                                          project_name)
    # merge existing events table with updates
    merge_result = bigquery_merge_updates_into_events_table_op(transform_result.output, events_table, project_name)
    # aggregate total by retaining only the most recent status per installation
    aggregate_result = bigquery_aggregate_events_op(transform_result.output, aggregation_table, project_name)
    # add custom properties to aggregation table
    add_custom_properties_result = bigquery_add_custom_properties(aggregate_result.output, project_name)
    # clean up firestore
    firestore_cleanup(firestore_database, firestore_collection, platform, aggregate_result.output, service_account,
                      project_name)
    # clean up firestore export
    cleanup_storage_export_intermediate(import_bucket, move_result.output).after(add_custom_properties_result,
                                                                                 merge_result)
    # clean up raw data set in bigquery
    cleanup_bigquery_raw_data_intermediate(import_result.output, project_name).after(add_custom_properties_result,
                                                                                     merge_result)
    # clean up transformed dataset in bigquery
    cleanup_bigquery_structured_data_intermediate(transform_result.output, project_name).after(
        add_custom_properties_result, merge_result)
