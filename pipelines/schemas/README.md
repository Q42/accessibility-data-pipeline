### Prerequisites:
- Create an `organisations.json` file in this directory containing the following schema:
```
{
  "organisations": ["example_org_1", "example_org_2"]
}
```

### To download a schema:
- Run: `bq show --format=prettyjson <project>:<dataset>.<table>`
- Select the content of field `schema.fields`

### To edit a specific schema:
- run `bq show --format=prettyjson <project>:<dataset>.<table>`
- Edit `schema.fields`
- Run `bq update <project>:<dataset>.<table> <schema_file>`

### To update all schema's:
- Edit the fields for both the aggregated and events version of the tables
- Run `update_table_schemas.py`. This script makes use of the same virtualenv as the pipeline