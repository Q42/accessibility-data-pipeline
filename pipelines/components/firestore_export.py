from kfp.v2.dsl import component


@component(packages_to_install=["google-cloud-firestore==2.3.4"])
def firestore_export_op(firestore_database: str, firestore_collection: str, export_bucket: str,
                        organisation_identifier: str, platform: str, pipeline_version: str,
                        service_account: dict) -> str:
    from google.cloud import firestore_admin_v1

    def get_firestore_admin_client(service_account):
        if not service_account:
            return firestore_admin_v1.FirestoreAdminClient()
        else:
            return firestore_admin_v1.FirestoreAdminClient.from_service_account_info(service_account)

    print(f"Firestore: starting export")
    client = get_firestore_admin_client(service_account)

    # Prepare export job
    firestore_db = client.database_path(firestore_database, "(default)")
    gcs_path = f"gs://{export_bucket}/firestore-exports/{organisation_identifier}-{platform}-{pipeline_version}"
    export_request = firestore_admin_v1.ExportDocumentsRequest(
        name=firestore_db,
        collection_ids=[firestore_collection],
        output_uri_prefix=gcs_path)

    # Start export and wait for result
    operation = client.export_documents(
        request=export_request,
    )
    result = operation.result()
    print(f"Export finished: {result.output_uri_prefix}")

    return result.output_uri_prefix
