# Channels Overview

Our channels/websocket implementation handles the communication between AWX API and updates in AWX UI.

## Architecture

AWX enlists the help of the `django-channels` library to create our communications layer. `django-channels` provides us with per-client messaging integration in our application by implementing the Asynchronous Server Gateway Interface (ASGI).

To communicate between our different services we use websockets. Every AWX node is fully connected via a special websocket endpoint that forwards any local websocket data to all other nodes. Local websockets are backed by Redis, the channels2 default service.

Inside AWX we use the `emit_channel_notification` function which places messages onto the queue. The messages are given an explicit event group and event type which we later use in our wire protocol to control message delivery to the client.

### Broadcast Backplane

Previously, AWX leveraged RabbitMQ to deliver Ansible events that emanated from one AWX node to all other AWX nodes so that any client listening and subscribed to the Websockets could get events from any running playbook. We are since moved off of RabbitMQ and onto a per-node local Redis instance. To maintain the requirement that any Websocket connection can receive events from any playbook running on any AWX node we still need to deliver every event to every AWX node. AWX does this via a fully connected Websocket backplane. 

#### Broadcast Backplane Token

AWX node(s) connect to every other node via the Websocket backplane. The backplane websockets initiate from the `wsbroadcast` process and connect to other nodes via the same nginx process that serves webpage websocket connections and marshalls incoming web/API requests. If you have configured AWX to run with an ssl terminated connection in front of nginx then you likely will have nginx configured to handle http traffic and thus the websocket connection will flow unencrypted over http. If you have nginx configured with ssl enabled, then the websocket traffic will flow encrypted.

Authentication is accomplished via a shared secret that is generated and set at playbook install time. The shared secret is used to derive a payload that is exchanged via the http(s) header `secret`. The shared secret payload consists of a a `secret`, containing the shared secret, and a `nonce` which is used to mitigate replay attack windows.

Note that the nonce timestamp is considered valid if it is within `300` second threshold. This is to allow for machine clock skews.
```
{
    "secret": settings.BROADCAST_WEBSOCKET_SECRET,
    "nonce": time.now()
}
```

The payload is encrypted using `HMAC-SHA256` with `settings.BROADCAST_WEBSOCKET_SECRET` as the key. The final payload that is sent, including the http header, is of the form: `secret: nonce_plaintext:HMAC_SHA256({"secret": settings.BROADCAST_WEBSOCKET_SECRET, "nonce": nonce_plaintext})`.

Upon receiving the payload, AWX decrypts the `secret` header using the known shared secret and ensures the `secret` value of the decrypted payload matches the known shared secret, `settings.BROADCAST_WEBSOCKET_SECRET`. If it does not match, the connection is closed. If it does match, the `nonce` is compared to the current time. If the nonce is off by more than `300` seconds, the connection is closed. If both tests pass, the connection is accepted.

## Protocol

You can connect to the AWX channels implementation using any standard websocket library by pointing it to `/websocket`. You must
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

**Note:** The deployment of AWX changes slightly with the introduction of `django-channels` and websockets. There are some minor differences between production and development deployments that will be pointed out in this document, but the actual services that run the code and handle the requests are identical between the two environments.

### Services
| Name        | Details |
|:-----------:|:-----------------------------------------------------------------------------------------------------------:|
| `nginx`     | listens on ports 80/443, handles HTTPS proxying, serves static assets, routes requests for `daphne` and `uwsgi` |
| `uwsgi`      | listens on port 8050, handles API requests |
| `daphne`      | listens on port 8051, handles websocket requests |
| `wsbroadcast`   | no listening port, forwards all group messages to all cluster nodes |
| `supervisord` | (production-only) handles the process management of all the services except `nginx` |

When a request comes in to `nginx` and has the `Upgrade` header and is for the path `/websocket`, then `nginx` knows that it should be routing that request to our `daphne` service.

`daphne` handles websocket connections proxied by nginx.

`wsbroadcast` fully connects all cluster nodes via the `/websocket/broadcast/` endpoint to every other cluster nodes. Sends a copy of all group websocket messages to all other cluster nodes (i.e. job event type messages).

### Development
 - `nginx` listens on 8013/8043 instead of 80/443
