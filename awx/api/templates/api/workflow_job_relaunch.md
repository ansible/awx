Relaunch a workflow job:

Make a POST request to this endpoint to launch a workflow job identical to the parent workflow job. This will spawn jobs, project updates, or inventory updates based on the unified job templates referenced in the workflow nodes in the workflow job. No POST data is accepted for this action.

If successful, the response status code will be 201 and serialized data of the new workflow job will be returned.