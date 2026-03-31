import subprocess
from datetime import datetime
from pathlib import Path


def archive_and_update_table_schema(table_name: str, archive_table_name: str, schema_file: Path):
    # First archive the table
    archive_result = subprocess.run(["bq","cp","-f",table_name,archive_table_name])

    if archive_result.returncode != 0:
        print(f"❌ Something went wrong, skipping `{table_name}` update")
        return

    print(f"✅ Successfully archived {table_name} to {archive_table_name}")

    # Only update the schema if the archive was successful
    update_result = subprocess.run(["bq","update",table_name,schema_file.absolute()])

    if update_result.returncode != 0:
        print(f"❌ Something went wrong while updating {table_name} schema")
        return

    print(f"✅ Successfully updated {table_name} schema")

def update_table_schemas(platform: str, organisation: str, project_name: str, pipeline_version: str, schemas_dir: Path):
    aggregated_schema = schemas_dir / f"generated/aggregated-schema-{platform}.json"
    event_schema = schemas_dir / f"generated/event-schema-{platform}.json"

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    aggregated_table_name = f"{project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}"
    event_table_name = f"{project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}"
    aggregated_archive_table_name = f"{project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}_archive_{current_time}"
    event_archive_table_name = f"{project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}_archive_{current_time}"

    archive_and_update_table_schema(aggregated_table_name, aggregated_archive_table_name, aggregated_schema)
    archive_and_update_table_schema(event_table_name, event_archive_table_name, event_schema)
