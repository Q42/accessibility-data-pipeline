from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-firestore==2.19.0", "google-cloud-bigquery==3.27.0"],
    base_image="python:3.13"
)
def firestore_cleanup(firestore_database: str, firestore_collection_id: str, platform: str, aggregation_table: str,
                      service_account: dict, project_name: str):
    from google.cloud import firestore
    from google.cloud import bigquery

    def get_firestore_client(firestore_database, service_account):
        if not service_account:
            return firestore.Client(project=firestore_database)
        else:
            return firestore.Client(project=firestore_database).from_service_account_info(service_account)

    # initialize BigQuery db client
    bigquery_client = bigquery.Client(project=project_name)
    # find the highest timestamp in the aggregated table
    query_job = bigquery_client.query(f"SELECT MAX(stats_timestamp) FROM {aggregation_table}")
    # parse query result. Keep only the first result
    query_result = query_job.result()
    max_timestamp = [row[0] for row in query_result][0]
    print(f"Latest timestamp: {max_timestamp}", flush=True)

    # initialize firestore db client
    firestore_client = get_firestore_client(firestore_database, service_account)
    timestamp_property_name = "Stats timestamp" if platform == "android" else "Stats_timestamp"
    batch_number = 0
    batch_size = 500
    running = True
    batch = firestore_client.batch()
    while running:
        # query 500 documents that have a timestamp lower than the maximum timestamp from aggregation table
        batch_number += 1
        data = firestore_client.collection(firestore_collection_id).where(f'currentMeasurement.`{timestamp_property_name}`', '<=',
                                                                          str(max_timestamp)).limit(batch_size)
        # check if the next document from the data stream is empty to stop the cleanup
        if next(data.stream(), None) is None:
            running = False

        # iterate through data stream and delete documents that match organisation_identifier
        for i, doc in enumerate(data.stream()):
            batch.delete(doc.reference)
        batch.commit()

        if batch_number % 10 == 0 or not running:
            print(
                f"COMPLETED: Batch number: {batch_number}. Total documents deleted: {batch_number * batch_size}. "
                f"Amount of docs in stream: {i + 1}, Doc that has been deleted: {str(doc.id)}", flush=True)
