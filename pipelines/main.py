import json
from pathlib import Path

from utils.generate_schemas import generate_schema_jsons
from utils.schema import load_schema

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
    print("2. Exit")


    choice = input("Enter your choice: ")

    match choice:
        case "1":
            for platform, typed_schema in schema_by_platform.items():
                generate_schema_jsons(platform, typed_schema, schemas_dir)
        case _:
            exit()
