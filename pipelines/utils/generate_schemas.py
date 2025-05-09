import json
from pathlib import Path
from .schema import SchemaField

def generate_aggregated_schema(platform: str, schema: list[SchemaField]):
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

    return fields

def generate_event_schema(schema: list[SchemaField]):
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

    return fields

# Writes data to a json file with proper formatting
def write_schema_to_file(file_name: str, data):
    with open(file_name, "w") as schema_file:
        json.dump(data, schema_file, indent=2)
        schema_file.write("\n")

def generate_schema_jsons(platform: str, typed_schema: list[SchemaField], schemas_dir: Path):
    print(f"Generating schemas for {platform} platform...")

    write_schema_to_file(schemas_dir / f"generated/aggregated-schema-{platform}.json", generate_aggregated_schema(platform, typed_schema))
    write_schema_to_file(schemas_dir / f"generated/event-schema-{platform}.json", generate_event_schema(typed_schema))
