from kfp.v2.dsl import component

@component
def storage_move_files_op(source_bucket_name: str, dest_bucket_name: str, export_uri: str, project_name: str) -> str:
    from google.cloud import storage

    if source_bucket_name == dest_bucket_name:
        print(f"Skip moving files, source and destination buckets are the same")
        return export_uri

    storage_client = storage.Client(project=project_name)
    source_bucket = storage_client.bucket(source_bucket_name)
    dest_bucket = storage_client.bucket(dest_bucket_name)
    folder = export_uri.split(f"gs://{source_bucket_name}/")[1]
    prefix = f"{folder}/"
    
    print(f"Storage: start moving files from: gs://{source_bucket_name}/{folder}", flush=True)
    blobs = list(source_bucket.list_blobs(prefix=prefix))
    
    print(f"Moving {len(blobs)} files", flush=True)
    for blob in blobs:
        source_bucket.copy_blob(blob, dest_bucket)
        blob.delete()

    print(f"Finished! Moved {len(list(dest_bucket.list_blobs(prefix=prefix)))} files")

    return f"gs://{dest_bucket_name}/{folder}"
