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
            print("This will update table schemas for the following tables:")
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
