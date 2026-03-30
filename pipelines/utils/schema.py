from dataclasses import dataclass
from pathlib import Path
import json
import os

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

def load_schema(platform: str, schemas_dir) -> list[SchemaField]:
    with open(schemas_dir / f"schema-{platform}.json", "r") as schema_file:
        schema = json.load(schema_file)

    typed_schema: list[SchemaField] = []

    for field in schema:
        typed_schema.append(SchemaField(
            name=field["name"],
            type=field["type"] if "type" in field else "STRING",
            mode=field["mode"] if "mode" in field else None,
        ))

    return typed_schema
