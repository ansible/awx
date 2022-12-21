# Bulk Job Launch

This endpoint allows the client to launch multiple UnifiedJobTemplates at a time, along side any launch time parameters that they would normally set at launch time.

Example:

```
{
"name": "my bulk job",
"jobs": [
    {"unified_job_template": 7, "inventory": 2},
    {"unified_job_template": 7, "credentials": [3]}
]

}
```
