{% ifmeth GET %}
# Determine if a Job can be canceled

Make a GET request to this resource to determine if the job can be canceled.
The response will include the following field:

* `can_cancel`: Indicates whether this job can be canceled (boolean, read-only)
{% endifmeth %}

{% ifmeth POST %}
# Cancel a Job
Make a POST request to this resource to cancel a pending or running job.  The
response status code will be 202 if successful, or 405 if the job cannot be
canceled.
{% endifmeth %}
