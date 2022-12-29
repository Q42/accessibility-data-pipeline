# Accessibility pipeline

This project facilitates the greater part of an initiative to gather information about usage of accessibility settings on mobile phones.
The process is currently used for iOS and Android for several different organisations. 
Ultimately the results of different organisations can be combined to create insights into accessibility setting usage by mobile users. 
Q42 currently provides this data to the collaborating organisations using dashboards. 
The data is also used to supply https://appt.org with relevant accessibility statistics.

![Schematic image of the accessibility pipeline](pipeline_overview.png?raw=true "Pipeline Overview")


## The process
The entire process consists of three main components.

### 1. The mobile library
The mobile library component is embedded in applications and reads user settings in regard to accessibility settings.
Currently the following two libraries are being used:
1. [Q42Stats for iOS](https://github.com/Q42/Q42Stats)
2. [Q42Stats for Android](https://github.com/Q42/Q42Stats.Android)

### 2. The API
A Flask API that handles requests send by the mobile library. It performs basic validation of the requests and passes the request body in its entirety to the correct Firestore collection.

### 3. The vertex AI pipeline
Initiated by Cloud Scheduler and Cloud Functions a nightly Vertex AI pipeline job is executed. The pipeline job is compiled using Kubeflow.
#### 3.1 From firestore to a Bigquery update table
Initially the Firebase export function is called to export data to Cloud Storage. Afterwards this export can be imported into Bigquery. 
Once the data is in a Bigquery table the data is cast to a different type and stored in a typed updates table.
#### 3.2 From the Bigquery updates table to the events table
Data is gathered fully anonymously. To accomplish this the decision has been made to refrain from using unique identifiers or otherwise privacy-sensitive information.
To be able to apply updates to the aggregation table we've introduced the concept of _current measurements_ and _previous measurements_.
Individual update requests always consist of a _current measurement_ and optionally contain a _previous measurement_. 
When inserting a new event a hash is made of both the current and previous measurement. 
#### 3.3 From the Bigquery updates table to the aggregation table
When applying an update the current measurement can be immediately inserted. 
In the case of the previous measurement the hash is used to delete the first corresponding row from the events table.
#### 3.4 Additional properties
Based on the data in the aggregations certain interpretations can be made. 
In our case we have added two properties that determine the most common values for certain Android devices to make an estimate of the default content size. 
Once an estimate has been made of the default content size one can determine whether a given data event has a content size larger or smaller than the default.
#### 3.5 Cleaning up
Once the before mentioned stages have been finished a series of cleanup components clean up the different data stores.

## Cloud tools
- Vertex AI Pipelines: https://console.cloud.google.com/vertex-ai/training/training-pipelines
- BigQuery: https://console.cloud.google.com/bigquery
- Scheduler: https://console.cloud.google.com/cloudscheduler
- Functions: https://console.cloud.google.com/functions/list
- Storage:
  - Pipeline run data: https://console.cloud.google.com/storage/browser/
  - Firestore exports: https://console.cloud.google.com/storage/browser/
- Alerting: https://console.cloud.google.com/monitoring/alerting/policies

## Setup
### Setting up storage
A plethora of data storages is used which require some setup.

#### Google cloud
Create a Google Cloud [project](https://developers.google.com/workspace/guides/create-project)
#### Firestore
Create a collection to store requests. We use one collection for iOS and one collection for Android.
_We work with one organisation that maintains their own Firestore collection. 
We therefore have added distinct behaviour in our API and pipeline to also incorporate data from this collection. 
This especially impacts the authentication processes._
#### Google Cloud Storage
1. Create a storage container in Google Cloud Storage.
2. Create a settings.json file in the root of the project which contains two keys: `project_name` and `storage_bucket` accompanied by the name of your Google project and the created storage bucket. 
#### Bigquery 
1. Create an events table per operating system per organisation
2. Create an aggregation table per operating system per organisation

### Setting up functionality
#### Deploy the API
Documentation on how to deploy the API can be found in the readme in the api directory.
#### Deploy a first build of the pipeline
Deploy a cron job per operating system
For more information take a look at the readme in the pipelines directory 
#### Setup Cloud scheduler
1. Go to the [cloud scheduler](https://console.cloud.google.com/cloudscheduler)
2. Create a new job
3. Configure timings and such as desired
4. Under configure the execution:
   1. Set url to the cloud function that was created by deploying the cron job
   2. Place the pipeline settings in the body. (An empty example can be found in pipelines/config. Documentation for the parameters can be found in pipelines/pipelines/pipeline_ios.py)

## Contact

- Johan Huijkman (Accessibility Engineer) - johan@q42.nl 
- Leonard Punt (Pipeline Engineer) - leonard@q42.nl
- Joris Bruil (Pipeline Engineer) - joris@q42.nl 
