# Channels Overview

Our channels/websocket implementation handles the communication between Tower API and updates in Tower UI.

## Architecture

Tower enlists the help of the `django-channels` library to create our communications layer. `django-channels` provides us with per-client messaging integration in our application by implementing the Asynchronous Server Gateway Interface (ASGI).

To communicate between our different services we use RabbitMQ to exchange messages. Traditionally, `django-channels` uses Redis, but Tower uses a custom `asgi_amqp` library that allows access to RabbitMQ for the same purpose.

Inside Tower we use the `emit_channel_notification` function which places messages onto the queue. The messages are given an explicit event group and event type which we later use in our wire protocol to control message delivery to the client.

## Protocol

You can connect to the Tower channels implementation using any standard websocket library by pointing it to `/websocket`. You must
provide a valid Auth Token in the request URL.

Once you've connected, you are not subscribed to any event groups. You subscribe by sending a `json` request that looks like the following:

    'groups': {
            'jobs': ['status_changed', 'summary'],
            'schedules': ['changed'],
            'ad_hoc_command_events': [ids...],
            'job_events': [ids...],
            'workflow_events': [ids...],
            'project_update_events': [ids...],
            'inventory_update_events': [ids...],
            'system_job_events': [ids...],
            'control': ['limit_reached_<user_id>'],
    }

These map to the event group and event type that the user is interested in. Sending in a new groups dictionary will clear all previously-subscribed groups before subscribing to the newly requested ones. This is intentional, and makes the single page navigation much easier since users only need to care about current subscriptions.

## Deployment

This section will specifically discuss deployment in the context of websockets and the path those requests take through the system.

**Note:** The deployment of Tower changes slightly with the introduction of `django-channels` and websockets. There are some minor differences between production and development deployments that will be pointed out in this document, but the actual services that run the code and handle the requests are identical between the two environments.

### Services
| Name        | Details |
|:-----------:|:-----------------------------------------------------------------------------------------------------------:|
| `nginx`     | listens on ports 80/443, handles HTTPS proxying, serves static assets, routes requests for `daphne` and `uwsgi` |
| `uwsgi`      | listens on port 8050, handles API requests |
| `daphne`      | listens on port 8051, handles websocket requests |
| `runworker`   | no listening port, watches and processes the message queue |
| `supervisord` | (production-only) handles the process management of all the services except `nginx` |

When a request comes in to `nginx` and has the `Upgrade` header and is for the path `/websocket`, then `nginx` knows that it should be routing that request to our `daphne` service.

`daphne` receives the request and generates channel and routing information for the request. The configured event handlers for `daphne` then unpack and parse the request message using the wire protocol mentioned above. This ensures that the connection has its context limited to only receive messages for events it is interested in. `daphne` uses internal events to trigger further behavior, which will generate messages and send them to the queue, which is then processed by the `runworker`.

`runworker` processes the messages from the queue. This uses the contextual information of the message provided by the `daphne` server and our `asgi_amqp` implementation to broadcast messages out to each client.

### Development
 - `nginx` listens on 8013/8043 instead of 80/443
