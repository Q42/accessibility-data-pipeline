# Accessibility pipeline API

This API is used to parse accessibility settings submitted by the clients.
It returns the current version of the data collection so the client knows the most recent version.
The request body contains an API key and the actual content of the settings.
The API key is checked with the main key stored in the Google Cloud key vault.
Afterwards the schema of the settings content is validated and stored in Firestore.

# Using the API

**Methods**

The API has one method: `/add` which takes a Firestore collection ID plus version as argument.

**Security**

Furthermore, the API requires the API key to be passed in the header as `X-Api-Key` . The API key is stored in the secret manager of the Google Cloud Console.
Steps:

- Open [Google Cloud Platform](https://console.cloud.google.com/home/dashboard) (select the correct project)
- On the platform search for and open `secret manager`
- Select `flask-api-key`
- The key can be found by selecting `View secret value` under `Actions`

**Request body**

The API requires the body to always contain at least a `currentMeasurement`.
This should be the case when a new installation is being registered.
When posting an update a `previousMeasurement` should be included as well.
Both `currentMeasurement` and `previousMeasurement` should contain only fields as listed below for iOS and Android respectively.
The API doesn't check what's in the values of the properties and these can may therefore be left empty.

The fields of iOS and Android are as follows (subject to regular change):

**[iOS Properties](schemas/ios.json)**

**[Android](schemas/android.json)**

# Prerequisites local development

- [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- Install dependencies: `uv sync`
  - This will automatically create a venv for you
- Create a secrets directory
- Add `configurations.json` containing the relevant `project_name` and relevant `collections` as list
- Start app: `uv run main.py`


# Deploying a new version of the API

- Make sure the `requirements.txt` is up-to-date with `uv export --frozen --no-dev -o requirements.txt`
- Make sure the secrets from 1PW are in `secrets/` (`configuration.json` and relevant service account JSONs)
- To deploy API, run: `gcloud app deploy --no-promote`
  - Once deploy is complete, enable traffic split; send a few percent of the traffic to the new version
  - Check if any errors occur; if new version is running fine, send all traffic to new version
- Activating/deactivating the API is done in the Google Cloud console: Google Cloud App Engine > Services > Enable/ Disable application
