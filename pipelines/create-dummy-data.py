import json
import sys
import random
import time
from args import get_platform_from_args, get_project_from_args

# Parse cmdline args
platform = get_platform_from_args(sys.argv)
project = get_project_from_args(sys.argv)

# load universal pipeline settings
with open("config.json", "r") as config_file:
    config = json.load(config_file)

with open("../settings.json", "r") as settings_file:
    settings = json.load(settings_file)

project_name = settings["project_name"]

with open(f"../pipelines/config/{platform}-{project}.json", 'r') as f:
    org_config = json.load(f)

firestore_collection = org_config["firestore_collection"]

from google.cloud import firestore

# Create a reference to the Firestore database
db = firestore.Client(project=project_name)

with open(f"schemas/schema-{platform}.json") as f:
    schema = json.load(f)

def create_dummy_data(schema):
    dummy_data = dict()

    for field in schema:
        if field["event_name"] in ["Stats timestamp", "Stats_timestamp"]:
            dummy_value = str(time.time())
        elif "mode" in field and field["mode"] == "REPEATED":
            dummy_value = []
            for _ in range(random.randint(1, 3)):
                dummy_value.append(random.choice(["foo", "bar", "baz"]))

            dummy_value = f"[{', '.join(dummy_value)}]"
        elif field["type"] == "INTEGER":
            dummy_value = str(random.randint(0, 100))
        elif field["type"] == "BOOLEAN":
            dummy_value = str(random.choice([True, False])).lower()
        else:
            dummy_value = random.choice(["foo", "bar", "baz"])

        dummy_data[field["event_name"]] = dummy_value

    if "Stats_version" in dummy_data:
        dummy_data["Stats_version"] = "Android 2023-09-08"

    if "Stats Model Version" in dummy_data:
        dummy_data["Stats Model Version"] = "4"

    return {
        "currentMeasurement": dummy_data
    }

for i in range(10):
    dummy_data = create_dummy_data(schema)
    db.collection(firestore_collection).add(dummy_data)
