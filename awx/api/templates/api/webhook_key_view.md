Webhook Secret Key:

Make a GET request to this resource to obtain the secret key for a job
template or workflow job template configured to be triggered by
webhook events.  The response will include the following fields:

* `webhook_key`: Secret key that needs to be copied and added to the
  webhook configuration of the service this template will be receiving
  webhook events from (string, read-only)

Make an empty POST request to this resource to generate a new
replacement `webhook_key`.
