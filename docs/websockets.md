# Channels Overview

Our channels/websocket implementation handles the communication between AWX API and updates in AWX UI. Note that the websockets are not meant for external use and 3rd party clients.

## Architecture

AWX enlists the help of the `django-channels` library to create our communications layer. `django-channels` provides us with per-client messaging integration in our application by implementing the Asynchronous Server Gateway Interface (ASGI).

**TODO: The information previously contained within this document has become outdated. This document will be rewritten in the near future.**
