# app.py

# Required imports
import json
import os
import time
from flask import Flask, request, jsonify, g
from google.cloud import firestore
from google.cloud import secretmanager

# Initialize Flask app
app = Flask(__name__)

with open("schemas/ios.json", "r") as ios_file:
    ios_properties = json.load(ios_file).keys()
with open("schemas/android.json", "r") as android_file:
    android_properties = json.load(android_file).keys()
with open("secrets/configurations.json", "r") as configurations_file:
    configurations = json.load(configurations_file)
    narwhal_configuration = configurations["narwhal"]
    meerkat_configuration = configurations["meerkat"]

# Fetch API secret
secrets_manager = secretmanager.SecretManagerServiceClient()
secret = secrets_manager.access_secret_version(
    request={"name": f"projects/{meerkat_configuration['project_name']}/secrets/flask-api-key/versions/1"}
).payload.data.decode("utf-8")

allowed_internal_collections = meerkat_configuration["collections"]
allowed_external_collections = narwhal_configuration["collections"]

allowed_collections = allowed_internal_collections + allowed_external_collections
print(allowed_collections)


def check_request(content):
    """
    Check for the presence of a complete set of properties in either the new or old settings.
    """
    current_properties = set(content["currentMeasurement"].keys())
    if "previousMeasurement" in content.keys():
        previous_properties = set(content["previousMeasurement"].keys())
        return validate_schema(previous_properties) and validate_schema(
            current_properties
        )
    return validate_schema(current_properties)


# Check whether properties match with either ios or android
def validate_schema(properties):
    """
    Validate whether the properties belong to either android or ios.
    The request body must contain at least the properties specified in the schema directory
    """
    if set(properties).issubset(android_properties) or set(properties).issubset(ios_properties):
        return True
    return False


def get_conn(db: str):
    """Use this function to establish or get the already established
    connection during a request. The connection is closed at the end
    of the request. This avoids having a global connection by storing
    the connection on the g object per request.
    """
    if "db" not in g:
        if db == "external_db":
            with open(f"secrets/{narwhal_configuration['service_account_file']}") as external_service_account_json:
                service_account = json.load(external_service_account_json)
                g.db = firestore.Client(project=narwhal_configuration["project_name"])\
                    .from_service_account_info(service_account)
        elif db == "internal_db":
            g.db = firestore.Client(project=meerkat_configuration["project_name"])
    return g.db


@app.teardown_request
def close_conn(e):
    """Automatically close the connection after the request if
    it was opened.
    """
    conn = g.pop("db", None)

    if conn is not None:
        conn.close()


@app.route("/add/<collection_id>", methods=["POST"])
def create(collection_id=None):
    """
    create() : Add document to Firestore collection with request body.
    The version based on the date (month and year) is returned as well as a result status
    """
    try:
        headers = request.headers
        api_key = headers.get("X-Api-Key")

        # Check API key
        if api_key != secret:
            return jsonify({"success": False, "Description": "Incorrect API key"}), 401

        if collection_id not in allowed_collections:
            return (
                jsonify(
                    {
                        "success": False,
                        "Description": f"Specified collection {collection_id} doesn't exist",
                    }
                ),
                400,
            )

        # parse request body
        body = request.json

        if "currentMeasurement" not in body.keys():
            return (
                jsonify(
                    {
                        "success": False,
                        "Description": f"'currentMeasurement' is missing",
                    }
                ),
                400,
            )

        if not check_request(body):
            invalid_properties = [
                prop
                for prop in body["currentMeasurement"]
                if prop not in ios_properties and prop not in android_properties
            ]
            if "previousMeasurement" in body:
                invalid_properties_previous = [
                    prop
                    for prop in body["previousMeasurement"]
                    if prop not in ios_properties and prop not in android_properties
                ]
                return (
                    jsonify(
                        {
                            "success": False,
                            "Description": "The api key was valid but the JSON schema was incorrect",
                            "Invalid properties currentMeasurement": invalid_properties,
                            "Invalid properties previousMeasurement": invalid_properties_previous,
                        }
                    ),
                    400,
                )
            return (
                jsonify(
                    {
                        "success": False,
                        "Description": "The api key was valid but the JSON schema was incorrect",
                        "Invalid properties": invalid_properties,
                    }
                ),
                400,
            )

        firestore_db = get_conn("external_db") if collection_id in allowed_external_collections else \
            get_conn("internal_db")
        doc_ref = firestore_db.collection(collection_id).document()
        doc_id = doc_ref.id
        doc_ref.set(body)

        # log doc current timestamp and doc id
        if 'Stats_timestamp' in body['currentMeasurement']:
            print({"timestamp": body['currentMeasurement']['Stats_timestamp'], "doc_id": doc_id})
        elif "Stats timestamp" in body['currentMeasurement']:
            print({"timestamp": body['currentMeasurement']['Stats timestamp'], "doc_id": doc_id})

        batch_id = str(time.strftime("%Y-%m"))
        return jsonify({"success": True, "batchId": batch_id}), 200

    except Exception as e:
        print(f"An Error Occurred: {e}")
        return 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
