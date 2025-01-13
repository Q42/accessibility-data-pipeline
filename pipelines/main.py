import json
import os
from pathlib import Path

from utils.update_table_schemas import update_table_schemas
from utils.schema import load_schema
from utils.generate_schemas import generate_schema_jsons
from utils.recompute_hashes import recompute_hashes

# load universal pipeline settings
with open("../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# load pipeline config
with open("config.json", "r") as config_file:
    config = json.load(config_file)

# load list of organisations
with open("organisations.json", "r") as organisations_file:
    organisations = json.load(organisations_file)["organisations"]

# pipeline version
pipeline_version = config["pipeline_version"]

# Google Cloud project name
project_name = settings["project_name"]

schemas_dir = Path("schemas")

schema_by_platform = {
    "ios": load_schema("ios", schemas_dir),
    "android": load_schema("android", schemas_dir)
}

while True:
    print("1. Generate schema JSONs")
    print("2. Recompute hashes")
    print("3. Update table schemas")
    print("4. Exit")


    choice = input("Enter your choice: ")

    match choice:
        case "1":
            for platform, typed_schema in schema_by_platform.items():
                generate_schema_jsons(platform, typed_schema, schemas_dir)
        case "2":
            print("This will recompute hashes for the following tables:")
            for organisation in organisations:
                for platform in schema_by_platform.keys():
                    print(f"- {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}")
                    print(f"- {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}")

            print("Are you sure you want to continue? [Y/n]")
            confirm = input().strip() or "Y"

            if confirm.lower() == "y":
                for organisation in organisations:
                    for platform, typed_schema in schema_by_platform.items():
                        recompute_hashes(platform, organisation, project_name, pipeline_version, typed_schema)
        case "3":
            print("This will recompute hashes for the following tables:")
            for organisation in organisations:
                for platform in schema_by_platform.keys():
                    print(f"- {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}")
                    print(f"- {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}")

            print("Are you sure you want to continue? [Y/n]")

            confirm = input().strip() or "Y"

            if confirm.lower() == "y":
                for organisation in organisations:
                    for platform, typed_schema in schema_by_platform.items():
                        update_table_schemas(platform, organisation, project_name, pipeline_version, schemas_dir)
        case _:
            exit()


















for platform, typed_schema in schema_by_platform.items():
    generate_schema_jsons(platform, typed_schema, schemas_dir)
    recompute_hashes

    for organisation in organisations:
        # Schemas are only updated if we are sure a back-up has been made
        cmd_line_aggregated_archive = f"bq cp -f {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.aggregated_data_{platform}_{pipeline_version}"

        if os.system(cmd_line_aggregated_archive) == 0:
            cmd_line_aggregated = f"bq update {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} generated/aggregated-schema-{platform}.json"
            os.system(cmd_line_aggregated)
        else:
            print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}` update")

        cmd_line_event_archive = f"bq cp -f {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.event_data_{platform}_{pipeline_version}"
        if os.system(cmd_line_event_archive) == 0:
            cmd_line_event = f"bq update {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} generated/event-schema-{platform}.json"
            os.system(cmd_line_event)
        else:
            print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}` update")
