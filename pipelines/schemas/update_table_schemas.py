from dataclasses import dataclass
import json
import os

with open("event-schema-android.json", "r") as android_schema_file:
    android_schema = json.load(android_schema_file)
with open("event-schema-ios.json", "r") as ios_schema_file:
    ios_schema = json.load(ios_schema_file)
with open("organisations.json", "r") as organisations_file:
    organisations = json.load(organisations_file)["organisations"]

@dataclass
class SchemaField:
    name: str
    type: str = "STRING"
    mode: str | None = None

    def to_dict(self):
        ret_val = {}

        if self.mode:
            ret_val["mode"] = self.mode

        ret_val["name"] = self.name
        ret_val["type"] = self.type

        return ret_val

def construct_aggregated_schema(platform: str, schema: list[SchemaField]):
    fields = [field.to_dict() for field in schema]

    fields.append({
        "name": "fields_hash",
        "type": "INTEGER"
    })

    if platform == "android":
        fields.append({
            "name": "screen_display_scale_default_comparison",
            "type": "STRING"
        })
        fields.append({
            "name": "screen_font_scale_default_comparison",
            "type": "STRING"
        })

    # Write result to aggregated-schema-{platform}.json
    with open(f"aggregated-schema-{platform}.json", "w") as aggregated_schema_file:
        json.dump(fields, aggregated_schema_file, indent=2)
        aggregated_schema_file.write("\n")

def construct_event_schema(platform: str, schema: list[SchemaField]):
    struct_fields = [field.to_dict() for field in schema]

    fields = [
        {
            "name": "doc_id",
            "type": "STRING"
        },
        {
            "fields": struct_fields,
            "name": "currentMeasurement",
            "type": "RECORD"
        },
        {
            "fields": struct_fields,
            "name": "previousMeasurement",
            "type": "RECORD"
        },
        {
            "name": "current_hash",
            "type": "INTEGER"
        },
        {
            "name": "previous_hash",
            "type": "INTEGER"
        }
    ]

    # Write result to event-schema-{platform}.json
    with open(f"event-schema-{platform}.json", "w") as event_schema_file:
        json.dump(fields, event_schema_file, indent=2)
        event_schema_file.write("\n")

def construct_schema_jsons(platform: str):
    with open(f"schema-{platform}.json", "r") as schema_file:
        schema = json.load(schema_file)

    typed_schema: list[SchemaField] = []

    for field in schema:
        typed_schema.append(SchemaField(
            name=field["name"],
            type=field["type"] if "type" in field else "STRING",
            mode=field["mode"] if "mode" in field else None,
        ))

    construct_aggregated_schema(platform, typed_schema)
    construct_event_schema(platform, typed_schema)

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

platforms = ["ios", "android"]

for platform in platforms:
    construct_schema_jsons(platform)

    for organisation in organisations:
        # Schemas are only updated if we are sure a back-up has been made
        cmd_line_aggregated_archive = f"bq cp -f {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.aggregated_data_{platform}_{pipeline_version}"

        if os.system(cmd_line_aggregated_archive) == 0:
            cmd_line_aggregated = f"bq update {project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version} aggregated-schema-{platform}.json"
            os.system(cmd_line_aggregated)
        else:
            print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}` update")

        cmd_line_event_archive = f"bq cp -f {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} {project_name}:pipeline_{organisation}_archive.event_data_{platform}_{pipeline_version}"
        if os.system(cmd_line_event_archive) == 0:
            cmd_line_event = f"bq update {project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version} event-schema-{platform}.json"
            os.system(cmd_line_event)
        else:
            print(f"Something went wrong, skipping `{project_name}:pipeline_{organisation}.event_data_{platform}_{pipeline_version}` update")
