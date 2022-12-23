import json
import os

with open("event-schema-android.json", "r") as android_schema_file:
    android_schema = json.load(android_schema_file)
with open("event-schema-ios.json", "r") as ios_schema_file:
    ios_schema = json.load(ios_schema_file)
with open("organisations.json", "r") as organisations_file:
    organisations = json.load(organisations_file)["organisations"]


# load universal pipeline settings
with open("../../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

# load universal pipeline settings
with open("../config.json", "r") as config_file:
    config = json.load(config_file)

# pipeline version
pipeline_version = config["pipeline_version"]

# Google Cloud project name
project_name = settings["project_name"]

operating_systems = ["ios", "android"]

for organisation in organisations:
    for system in operating_systems:
        cmd_line_aggregated_archive = f"bq cp -f {project_name}:pipeline_{organisation}.aggregated_data_{system}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.aggregated_data_{system}_{pipeline_version}"
        os.system(cmd_line_aggregated_archive)
        cmd_line_aggregated = f"bq update {project_name}:pipeline_{organisation}.aggregated_data_{system}_{pipeline_version} aggregated-schema-{system}.json"
        os.system(cmd_line_aggregated)
        cmd_line_event_archive = f"bq cp -f {project_name}:pipeline_{organisation}.event_data_{system}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.event_data_{system}_{pipeline_version}"
        os.system(cmd_line_event_archive)
        cmd_line_event = f"bq update {project_name}:pipeline_{organisation}.event_data_{system}_{pipeline_version} event-schema-{system}.json"
        os.system(cmd_line_event)