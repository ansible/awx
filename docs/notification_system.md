# Notification System Overview

A Notifier is an instance of a notification type (Email, Slack, Webhook, etc) with a name, description, and a defined configuration (A few examples: Username, password, server, recipients for the Email type.  Token and list of channels for Slack.  Url and Headers for webhooks)

A Notification is a manifestation of the Notifier... for example, when a job fails a notification is sent using the configuration defined by the Notifier.

This PR implements the Notification system as outlined in the 3.0 Notifications spec.  At a high level the typical flow is:

* User creates a Notifier at `/api/v1/notifiers`
* User assigns the notifier to any of the various objects that support it (all variants of job templates as well as organizations and projects) and at the appropriate trigger level for which they want the notification (error, success, or any).   For example a user may wish to assign a particular Notifier to trigger when `Job Template 1` fails.   In which case they will associate the notifier with the job template at `/api/v1/job_templates/n/notifiers_error`.

## Notifier hierarchy

Notifiers assigned at certain levels will inherit notifiers defined on parent objects as such:

* Job Templates will use notifiers defined on it as well as inheriting notifiers from the Project used by the Job Template and from the Organization that it is listed under (via the Project).
* Project Updates will use notifiers defined on the project and will inherit notifiers from the Organization associated with it.
* Inventory Updates will use notifiers defined on the Organization that it is listed under
* Ad-hoc commands will use notifiers defined on the Organization that the inventory is associated with

## Workflow

When a job succeeds or fails, the error or success handler will pull a list of relevant notifiers using the procedure defined above.  It will then create a Notification object for each one containing relevant details about the job and then **send**s it to the destination (email addresses, slack channel(s), sms numbers, etc).    These Notification objects are available as related resources on job types (jobs, inventory updates, project updates), and also at `/api/v1/notifications`.   You may also see what notifications have been sent from a notifier by examining its related resources.

Notifications can succeed or fail but that will not cause its associated job to succeed or fail.   The status of the notification can be viewed at its detail endpoint `/api/v1/notifications/<n>`

## Testing Notifiers before using them

Once a Notifier is created its configuration can be tested by utilizing the endpoint at `/api/v1/notifiers/<n>/test`   This will emit a test notification given the configuration defined by the Notifier.  These test notifications will also appear in the notifications list at `/api/v1/notifications`

# Notification Types

The currently defined Notification Types are:

* Email
* Slack
* Hipchat
* Mattermost
* Rocket.Chat
* Pagerduty
* Twilio
* IRC
* Webhook
* Grafana

Each of these have their own configuration and behavioral semantics and testing them may need to be approached in different ways.   The following sections will give as much detail as possible.

## Email

The email notification type supports a wide variety of smtp servers and has support for ssl/tls connections and timeouts.

### Testing considerations

The following should be performed for good acceptance:

* Test plain authentication
* Test SSL and TLS authentication
* Verify single and multiple recipients
* Verify message subject and contents are formatted sanely.  They should be plaintext but readable.

### Test Service

Either setup a local smtp mail service here are some options:

* postfix service on galaxy: https://galaxy.ansible.com/debops/postfix/
* Mailtrap has a good free plan and should provide all of the features we need under that plan: https://mailtrap.io/

## Slack

Slack is pretty easy to configure, it just needs a token which you can get from creating a bot in the integrations settings for the slack team.

### Testing considerations

The following should be performed for good acceptance:

* Test single and multiple channels and good formatting of the message.   Note that slack notifications only contain the minimal information

### Test Service

Any user of the Ansible slack service can create a bot integration (which is how this notification is implemented).   Remember to invite the bot to the channel first.

## Hipchat

There are several ways to integrate with hipchat.  The Tower implementation uses Hipchat "Integrations".  Currently you can find this at the bottom right of the main hipchat webview.  From there you will select "Build your own Integration".   After creating that it will list the `auth_token` that needs to be supplied to Tower.  Some other relevant details on the fields accepted by Tower for the Hipchat notification type:

* `color`: This will highlight the message as the given color.  If set to something hipchat doesn't expect then the notification will generate an error, but it's pretty rad.  I like green personally.
* `notify`: Selecting this will cause the bot to "notify" channel members.  Normally it will just be stuck as a message in the chat channel without triggering anyone's notifications.  This option will notify users of the channel respecting their existing notification settings (browser notification, email fallback, etc.)
* `message_from`: Along with the integration name itself this will put another label on the notification.  I reckon this would be helpful if multiple services are using the same integration to distinguish them from each other.
* `api_url`:  The url of the hipchat api service.  If you create a team hosted by them it'll be something like `https://team.hipchat.com`.   For a self-hosted service it'll be the http url that is accessible by Tower.

### Testing considerations

* Make sure all options behave as expected
* Test single and multiple channels
* Test that notification preferences are obeyed.
* Test formatting and appearance.  Note that, like Slack, hipchat will use the minimal version of the notification.
* Test standalone hipchat service for parity with hosted solution

### Test Service

Hipchat allows you to create a team with limited users and message history for free, which is easy to set up and get started with.   Hipchat contains a self-hosted server also which we should test for parity... it has a 30 day trial but there might be some other way to negotiate with them, redhat, or ansible itself:

https://www.hipchat.com/server

## Mattermost

The mattermost notification integration uses Incoming Webhooks. A password is not required because the webhook URL itself is the secret. Webhooks must be enabled in the System Console of Mattermost. If the user wishes to allow Ansible Tower notifications to modify the Icon URL and username of the notification then they must enabled these options as well.

In order to enable these settings in Mattermost:
1. First go to System Console > Integrations > Custom Integrations. Check Enable Incoming Webhooks
2. Optionally, go to System Console > Integrations > Custom Integrations. Check "Enable integrations to override usernames" and Check "Enable integrations to override profile picture icons"
3. Go to Main Menu > Integrations > Incoming Webhook. Click "Add Incoming Webhook"
4. Choose a "Display Name", "Description", and Channel. This channel will be overridden if the notification uses the `channel` option

* `url`: The incoming webhook URL that was configured in Mattermost. Notifications will use this URL to POST.
* `username`: Optional. The username to display for the notification.
* `channel`: Optional. Override the channel to display the notification in. Mattermost incoming webhooks are tied to a channel by default, so if left blank then this will use the incoming webhook channel. Note, if the channel does not exist then the notification will error out.
* `icon_url`: Optional. A URL pointing to an icon to use for the notification.

### Testing considerations

* Make sure all options behave as expected
* Test that all notification options are obeyed
* Test formatting and appearance. Mattermost will use the minimal version of the notification.

### Test Service

* Utilize an existing Mattermost installation or use their docker container here: `docker run --name mattermost-preview -d --publish 8065:8065 mattermost/mattermost-preview`
* Turn on Incoming Webhooks and optionally allow Integrations to override usernames and icons in the System Console.

## Rocket.Chat

The Rocket.Chat notification integration uses Incoming Webhooks. A password is not required because the webhook URL itself is the secret. An integration must be created in the Administration section of the Rocket.Chat settings.

The following fields are available for the Rocket.Chat notification type:
* `url`: The incoming webhook URL that was configured in Rocket.Chat. Notifications will use this URL to POST.
* `username`: Optional. Change the displayed username from Rocket Cat to specified username
* `icon_url`: Optional. A URL pointing to an icon to use for the notification.

### Testing considerations

* Make sure that all options behave as expected
* Test that all notification options are obeyed

### Test Service

* Utilize an existing Rocket.Chat installation or use their docker containers from https://rocket.chat/docs/installation/docker-containers/
* Create an Incoming Webhook in the Integrations section of the Administration settings


## Pagerduty

Pager duty is a fairly straightforward integration.   The user will create an API Key in the pagerduty system (this will be the token that is given to Tower) and then create a "Service" which will provide an "Integration Key" that will be given to Tower also.   The other options of note are:

* `subdomain`: When you sign up for the pagerduty account you will get a unique subdomain to communicate with.   For instance, if you signed up as "towertest" the web dashboard will be at towertest.pagerduty.com and you will give the Tower API "towertest" as the subdomain (not the full domain).
* `client_name`: This will be sent along with the alert content to the pagerduty service to help identify the service that is using the api key/service.  This is helpful if multiple integrations are using the same api key and service.

### Testing considerations

* Make sure the alert lands on the pagerduty service
* Verify that the minimal information is displayed for the notification but also that the detail of the notification contains all fields.  Pagerduty itself should understand the format in which we send the detail information.

### Test Service

Pagerduty allows you to sign up for a free trial with the service.   We may also have a ansible-wide pagerduty service that we could tie into for other things.

## Twilio

Twilio service is an Voice and SMS automation service.  Once you are signed in you'll need to create a phone number from which the message will be sent.  You'll then define a "Messaging Service" under Programmable SMS and associate the number you created before with it.  Note that you may need to verify this number or some other information before you are allowed to use it to send to any numbers.  The Messaging Service does not need a status callback url nor does it need the ability to Process inbound messages.

Under your individual (or sub) account settings you will have API credentials.   The Account SID and AuthToken are what will be given to Tower.   There are a couple of other important fields:

* `from_number`:  This is the number associated with the messaging service above and must be given in the form of "+15556667777"
* `to_numbers`: This will be the list of numbers to receive the SMS and should be the 10-digit phone number.

### Testing considerations

* Test notifications with single and multiple recipients
* Verify that the minimal information is displayed for the notification.  Note that this notification type does not display the full detailed notification.

### Test Service

Twilio is fairly straightforward to sign up for but I don't believe it has a free plan, a credit card will be needed to sign up for it though the charges are fairly minimal per message.

## IRC

The Tower irc notification takes the form of an IRC bot that will connect, deliver its messages to channel(s) or individual user(s), and then disconnect.  The Tower notification bot also supports SSL authentication.  The Tower bot does not currently support Nickserv identification.  If a channel or user does not exist or is not on-line then the Notification will not fail, the failure scenario is reserved specifically for connectivity.

Connectivity information is straightforward:

* `server`: The host name or address of the irc server
* `port`: The irc server port
* `nickname`: The bot's nickname once it connects to the server
* `password`: IRC servers can require a password to connect.  If the server doesn't require one then this should be an empty string
* `use_ssl`: Should the bot use SSL when connecting
* `targets`: A list of users and/or channels to send the notification to.

### Test Considerations

* Test both plain and SSL connectivity
* Test single and multiples of both users and channels.

### Test Service

There are a few modern irc servers to choose from but we should use a fairly full featured service to get good test coverage.   I recommend inspircd because it is actively maintained and pretty straightforward to configure.

## Webhook

The webhook notification type in Ansible Tower provides a simple interface to sending POSTs to a predefined web service.  Tower will POST to this address using `application/json` content type with the data payload containing all relevant details in json format.
The parameters are pretty straightforward:

* `url`: The full url that will be POSTed to
* `headers`: Headers in json form where the keys and values are strings.  For example: `{"Authentication": "988881adc9fc3655077dc2d4d757d480b5ea0e11", "MessageType": "Test"}`

### Test Considerations

* Test HTTP service and HTTPS, also specifically test HTTPS with a self signed cert.
* Verify that the headers and payload are present and that the payload is json and the content type is specifically `application/json`

### Test Service

A very basic test can be performed by using `netcat`:

```
netcat -l 8099
```

and then sending the request to:   http://\<host\>:8099

Note that this won't respond correctly to the notification so it will yield an error.   I recommend using a very basic Flask application for verifying the POST request, you can see an example of mine here:

https://gist.github.com/matburt/73bfbf85c2443f39d272

This demonstrates how to define an endpoint and parse headers and json content, it doesn't show configuring Flask for HTTPS but this is also pretty straightforward: http://flask.pocoo.org/snippets/111/


## Grafana

The Grafana notification type allows you to create Grafana annotations, Details about this feature of Grafana are available at http://docs.grafana.org/reference/annotations/. In order to allow Tower to add annotations an API Key needs to be created in Grafana. Note that the created annotations are region events with start and endtime of the associated Tower Job. The annotation description is also provided by the subject of the associated Tower Job, e.g.:
```
Job #1 'Ping Macbook' succeeded: https://towerhost/#/jobs/playbook/1
```

The configurable options of the Grafana notification type are:
* `Grafana URL`: The base URL of the Grafana server (required). **Note**: the /api/annotations endpoint will be added automatically to the base Grafana URL.
* `API Key`: The Grafana API Key to authenticate (required)
* `ID of the Dashboard`: To create annotations in a specific Grafana dashboard enter the ID of the dashboard (optional).
* `ID of the Panel`: To create annotations in a specific Panel enter the ID of the panel (optional).
**Note**: If neither dashboardId nor panelId are provided then a global annotation is created and can be queried in any dashboard that adds the Grafana annotations data source.
* `Annotations tags`: List of tags to add to the annotation. One tag per line.
* `Disable SSL Verification`: Disable the verification of the ssl certificate, e.g. when using a self-signed SSL certificate for Grafana.

### Test Considerations

* Make sure that all options behave as expected
* Test that all notification options are obeyed
* e.g. Make sure the annotation gets created on the desired dashboard and/or panel and with the configured tags

### Test Service
* Utilize an existing Grafana installation or use their docker containers from http://docs.grafana.org/installation/docker/
* Create an API Key in the Grafana configuration settings
* (Optional) Lookup dashboardId and/or panelId if needed
* (Optional) define tags for the annotation
