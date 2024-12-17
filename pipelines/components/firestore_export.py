from kfp.v2.dsl import component


@component(packages_to_install=["google-cloud-firestore==2.3.4"])
def firestore_export_op(firestore_database: str, firestore_collection: str, export_bucket: str,
                        organisation_identifier: str, platform: str, pipeline_version: str,
                        service_account: dict) -> str:
    from google.cloud import firestore_admin_v1
    from google.cloud import storage

    def get_firestore_admin_client(service_account):
        if not service_account:
            return firestore_admin_v1.FirestoreAdminClient()
        else:
            return firestore_admin_v1.FirestoreAdminClient.from_service_account_info(service_account)

    def get_storage_client(service_account):
        if not service_account:
            return storage.Client()
        else:
            return storage.Client.from_service_account_info(service_account)

    print(f"Firestore: starting export")
    firestore_client = get_firestore_admin_client(service_account)
    storage_client = get_storage_client(service_account)

    # Prepare export job
    firestore_db = firestore_client.database_path(firestore_database, "(default)")
    export_path = f"firestore-exports/{organisation_identifier}-{platform}-{pipeline_version}"
    gcs_path = f"gs://{export_bucket}/{export_path}"

    # Check if the directory exists and delete it if it does
    bucket = storage_client.bucket(export_bucket)
    blobs = bucket.list_blobs(prefix=f"firestore-exports/{organisation_identifier}-{platform}")
    for blob in blobs:
        blob.delete()
    print(f"Deleted existing files in {gcs_path}")

    export_request = firestore_admin_v1.ExportDocumentsRequest(
        name=firestore_db,
        collection_ids=[firestore_collection],
        output_uri_prefix=gcs_path)

    # Start export and wait for result
    operation = firestore_client.export_documents(
        request=export_request,
    )
    result = operation.result()
    print(f"Export finished: {result.output_uri_prefix}")

    return result.output_uri_prefix
