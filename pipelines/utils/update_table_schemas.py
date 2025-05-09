import os
from pathlib import Path

def update_table_schemas(platform: str, organisation: str, project_name: str, pipeline_version: str, schemas_dir: Path):
    aggregated_schema = schemas_dir / f"aggregated-schema-{platform}.json"
    event_schema = schemas_dir / f"event-schema-{platform}.json"

    # Schemas are only updated if we are sure a back-up has been made
    cmd_line_aggregated_archive = f"bq cp -f {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.aggregated_data_{platform}_{pipeline_version}"

    if os.system(cmd_line_aggregated_archive) == 0:
        cmd_line_aggregated = f"bq update {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} {aggregated_schema.absolute()}"
        os.system(cmd_line_aggregated)
    else:
        print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}` update")

    cmd_line_event_archive = f"bq cp -f {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.event_data_{platform}_{pipeline_version}"
    if os.system(cmd_line_event_archive) == 0:
        cmd_line_event = f"bq update {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} {event_schema.absolute()}"
        os.system(cmd_line_event)
    else:
        print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}` update")
