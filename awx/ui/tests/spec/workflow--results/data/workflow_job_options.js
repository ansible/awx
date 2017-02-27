export default {
    "name": "Workflow Job Detail",
    "description": "# Retrieve Workflow Job:\n\nMake GET request to this resource to retrieve a single workflow job\nrecord containing the following fields:\n\n* `id`: Database ID for this workflow job. (integer)\n* `type`: Data type for this workflow job. (choice)\n* `url`: URL for this workflow job. (string)\n* `related`: Data structure with URLs of related resources. (object)\n* `summary_fields`: Data structure with name/description for related resources. (object)\n* `created`: Timestamp when this workflow job was created. (datetime)\n* `modified`: Timestamp when this workflow job was last modified. (datetime)\n* `name`: Name of this workflow job. (string)\n* `description`: Optional description of this workflow job. (string)\n* `unified_job_template`:  (field)\n* `launch_type`:  (choice)\n    - `manual`: Manual\n    - `relaunch`: Relaunch\n    - `callback`: Callback\n    - `scheduled`: Scheduled\n    - `dependency`: Dependency\n    - `workflow`: Workflow\n    - `sync`: Sync\n* `status`:  (choice)\n    - `new`: New\n    - `pending`: Pending\n    - `waiting`: Waiting\n    - `running`: Running\n    - `successful`: Successful\n    - `failed`: Failed\n    - `error`: Error\n    - `canceled`: Canceled\n* `failed`:  (boolean)\n* `started`: The date and time the job was queued for starting. (datetime)\n* `finished`: The date and time the job finished execution. (datetime)\n* `elapsed`: Elapsed time in seconds that the job ran. (decimal)\n* `job_args`:  (string)\n* `job_cwd`:  (string)\n* `job_env`:  (field)\n* `job_explanation`: A status field to indicate the state of the job if it wasn&#39;t able to run and capture stdout (string)\n* `result_stdout`:  (field)\n* `execution_node`: The Tower node the job executed on. (string)\n* `result_traceback`:  (string)\n* `workflow_job_template`:  (field)\n* `extra_vars`:  (string)\n\n\n\n# Delete Workflow Job:\n\nMake a DELETE request to this resource to delete this workflow job.\n\n\n\n\n\n\n\n\n\n\n\n> _New in Ansible Tower 3.1.0_",
    "renders": [
        "application/json",
        "text/html"
    ],
    "parses": [
        "application/json"
    ],
    "actions": {
        "GET": {
            "id": {
                "type": "integer",
                "label": "ID",
                "help_text": "Database ID for this workflow job."
            },
            "type": {
                "type": "choice",
                "label": "Type",
                "help_text": "Data type for this workflow job.",
                "choices": [
                    [
                        "workflow_job",
                        "Workflow Job"
                    ]
                ]
            },
            "url": {
                "type": "string",
                "label": "Url",
                "help_text": "URL for this workflow job."
            },
            "related": {
                "type": "object",
                "label": "Related",
                "help_text": "Data structure with URLs of related resources."
            },
            "summary_fields": {
                "type": "object",
                "label": "Summary fields",
                "help_text": "Data structure with name/description for related resources."
            },
            "created": {
                "type": "datetime",
                "label": "Created",
                "help_text": "Timestamp when this workflow job was created."
            },
            "modified": {
                "type": "datetime",
                "label": "Modified",
                "help_text": "Timestamp when this workflow job was last modified."
            },
            "name": {
                "type": "string",
                "label": "Name",
                "help_text": "Name of this workflow job."
            },
            "description": {
                "type": "string",
                "label": "Description",
                "help_text": "Optional description of this workflow job."
            },
            "unified_job_template": {
                "type": "field",
                "label": "unified job template"
            },
            "launch_type": {
                "type": "choice",
                "label": "Launch type",
                "choices": [
                    [
                        "manual",
                        "Manual"
                    ],
                    [
                        "relaunch",
                        "Relaunch"
                    ],
                    [
                        "callback",
                        "Callback"
                    ],
                    [
                        "scheduled",
                        "Scheduled"
                    ],
                    [
                        "dependency",
                        "Dependency"
                    ],
                    [
                        "workflow",
                        "Workflow"
                    ],
                    [
                        "sync",
                        "Sync"
                    ]
                ]
            },
            "status": {
                "type": "choice",
                "label": "Status",
                "choices": [
                    [
                        "new",
                        "New"
                    ],
                    [
                        "pending",
                        "Pending"
                    ],
                    [
                        "waiting",
                        "Waiting"
                    ],
                    [
                        "running",
                        "Running"
                    ],
                    [
                        "successful",
                        "Successful"
                    ],
                    [
                        "failed",
                        "Failed"
                    ],
                    [
                        "error",
                        "Error"
                    ],
                    [
                        "canceled",
                        "Canceled"
                    ]
                ]
            },
            "failed": {
                "type": "boolean",
                "label": "Failed"
            },
            "started": {
                "type": "datetime",
                "label": "Started",
                "help_text": "The date and time the job was queued for starting."
            },
            "finished": {
                "type": "datetime",
                "label": "Finished",
                "help_text": "The date and time the job finished execution."
            },
            "elapsed": {
                "type": "decimal",
                "label": "Elapsed",
                "help_text": "Elapsed time in seconds that the job ran."
            },
            "job_args": {
                "type": "string",
                "label": "Job args"
            },
            "job_cwd": {
                "type": "string",
                "label": "Job cwd"
            },
            "job_env": {
                "type": "field",
                "label": "job_env"
            },
            "job_explanation": {
                "type": "string",
                "label": "Job explanation",
                "help_text": "A status field to indicate the state of the job if it wasn't able to run and capture stdout"
            },
            "result_stdout": {
                "type": "field",
                "label": "Result stdout"
            },
            "execution_node": {
                "type": "string",
                "label": "Execution node",
                "help_text": "The Tower node the job executed on."
            },
            "result_traceback": {
                "type": "string",
                "label": "Result traceback"
            },
            "workflow_job_template": {
                "type": "field",
                "label": "Workflow job template"
            },
            "extra_vars": {
                "type": "string",
                "label": "Extra vars"
            }
        }
    },
    "added_in_version": "3.1.0",
    "types": [
        "workflow_job"
    ]
}