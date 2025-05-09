## README:
- Schemas are generated from `schema-android.json` and `schema-ios.json`

### To download a schema:
- Run: `bq show --format=prettyjson <project>:<dataset>.<table>`
- Select the content of field `schema.fields`

### To add a property to a schema:
- Edit `schema-{platform}.json` to add the new property
- Run the CLI to update the schema

### To remove a property from a schema:
- Edit `schema-{platform}.json` to remove the property
- Run
  ```sql
  CREATE OR REPLACE TABLE `{project_name}.pipeline_{organisation}.[aggregated|event]_data_{platform}_{pipeline_version}` AS (
    SELECT * EXCEPT (`[PROPERTY_TO_DELETE]`) FROM `{project_name}.pipeline_{organisation}.[aggregated|event]_data_{platform}_{pipeline_version}`
  );
  ```


### To update all schema's:
- Edit the fields for both the aggregated and events version of the tables
- Run `update_table_schemas.py`. This script makes use of the same virtualenv as the pipeline
  - This script makes use of `bq update <project>:<dataset>.<table> <schema_file>` to update the schema

### To make a copy of a table:
For development purposes it might be convenient to create a test table
- `bq cp <project>:<dataset>.<table> <project>:<dataset>.<test_table_name>`
