from kfp.dsl import component

@component(
    packages_to_install=["google-cloud-storage==2.19.0"],
    base_image="python:3.13"
)
def cleanup_storage_export_intermediate(bucket_name: str, storage_uri_prefix: str):
    from google.cloud import storage

    print(f"Storage: delete export intermediate")
    folder = storage_uri_prefix.split(f"gs://{bucket_name}/")[1] + "/"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    bucket.delete_blobs(blobs=list(bucket.list_blobs(prefix=folder)))
    print(f"Delete finished")
