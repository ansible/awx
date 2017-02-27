# Cancel Workflow Job

Make a GET request to this resource to determine if the workflow job can be
canceled. The response will include the following field:

* `can_cancel`: Indicates whether this workflow job is in a state that can
  be canceled (boolean, read-only)

Make a POST request to this endpoint to submit a request to cancel a pending
or running workflow job.  The response status code will be 202 if the
request to cancel was successfully submitted, or 405 if the workflow job
cannot be canceled.
