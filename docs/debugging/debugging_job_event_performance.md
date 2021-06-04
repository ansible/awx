# AWX Job Event Performance Debugging

## The Job Event Critical Path

> Observed delay in UI job `stdout`.

Job events start their life in Ansible, specifically in the AWX Ansible callback plugin. AWX creates JSON payloads out of function calls and the parameters are passed to the registered callback plugin. The moment the JSON payload is created in the callback plugin is the `created` time on a job event record, which is then stored in the AWX database. The `modified` time is when the job event record was stored in the database. The difference in `modified - created` is the time it takes for an event to go from Ansible and into the AWX database. The pieces in between that path are:

  1. Ansible
  2. The AWX callback plugin (inside of `ansible-runner`)
  3. A push to Redis; this ends the processing that happens in the Ansible playbook process space
  4. The work then picks back up in the callback receiver process with a pop from Redis
  5. A bulk insert to `postgres` occurs
  6. Events are emitted over websocket via Redis
  7. At this point, the handling of the event changes process space to deliver over the websocket(s) via `daphne` to the other AWX nodes & to websocket browser clients
  8. The UI then gets the websocket event and displays it in the job details view

This is what we call the "critical path" for job events.

### Quick Debugging

* Log in to an AWX instance and open Chrome Debug Tools
* Paste in the contents of `debug.js` (found below) into the console
* You will notice a blue square on the screen with a textbox and a button
* Launch a job and note the job ID
* Enter the job ID into the textbox and click Submit; this will subscribe to the job events for that job
* The blue box should update with the current "lag" time in seconds. The lag time is the `now - created`. This represents the path from 4-8 listed above.
* Note, use the debug tool while hanging out on something OTHER THAN the job details page (path steps 4-7). Then, hang out on the Job Details page with the debug page (path steps 4-8) . Note the difference.

### Debugging the Websockets

AWX relies on Django channels and Redis for websockets. `channels_redis`, the connection plugin for channels to use Redis as the message backend, allows for setting per-group queue limits. By default, AWX sets this limit to 10,000. It can be tricky to know when this limit is exceeded due to the asynchronous nature of Channels + ASGI + websockets.

One way to be notified of websocket queue reaching capacity is to hook into the `channels_redis.core` logger. Below is an example of how to enable the logging and an example of what capacity overflow messages look like:

```
LOGGING['loggers']['channels_redis.core'] = {
    'handlers': ['console', 'file', 'tower_warnings'],
    'level': 'DEBUG'
}

tail -f /var/log/tower/tower.log
2021-04-28 20:53:51,230 INFO     channels_redis.core 1 of 4 channels over capacity in group broadcast-group_send
2021-04-28 20:53:51,231 INFO     channels_redis.core 1 of 1 channels over capacity in group job_events-49
```

The two above log messages were not chosen randomly. They are representative of common groups that can overflow. Each AWX node sends all events it processes locally to all other AWX nodes. It does this via the `broadcast-group_send` group; all AWX nodes are subscribed to this group. Under high load, this queue can overflow.

The other log message above is an overflow in the `job_events-49` group. Overflow in this queue can happen when either AWX or the websocket client cannot keep up with the event websocket messages.

```
redis-cli -s /var/run/redis/redis.sock

redis /var/run/redis/redis.sock> keys *
1) "awx_dispatcher_statistics"
2) "callback_tasks"
3) "broadcast_websocket_stats"
4) "awx_callback_receiver_statistics_105217"
5) "asgi:group:broadcast-group_send"
6) "asgispecific.2061d193ea1c4dd487d8f455dfeabd6a!"
```

Above is an example of all of the keys in Redis on an AWX node. Let's focus on 3) and 6). 3) is the special group we mentioned above. The Redis `ZSET` object is created by `channels_redis` to track Django Channel clients subscribed to the `broadcast-group_send` group. 6) is the queue that holds websocket messages.

```
redis /var/run/redis/redis.sock> zrange asgi:group:broadcast-group_send 0 -1
1) "specific.2061d193ea1c4dd487d8f455dfeabd6a!20e9f507dd78489b89eb2aeb153d3834"
2) "specific.2061d193ea1c4dd487d8f455dfeabd6a!ea4463175cbb4b04937b98941aae0731"
3) "specific.2061d193ea1c4dd487d8f455dfeabd6a!8b5249bcb61c4026a9d4e341afe98a56"
4) "specific.2061d193ea1c4dd487d8f455dfeabd6a!4854fb8c3d36442d95ff41a34fc5ee16"

redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 58
redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 29
redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 18
redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 3
redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 14
redis /var/run/redis/redis.sock> zcount asgispecific.2061d193ea1c4dd487d8f455dfeabd6a! -inf +inf
(integer) 15
```

In the above example we show how to get the list of Channels clients subscribed to the `broadcast-group_send` queue. We also show how to get the queue depth of a websocket message queue.

<details><summary>debug.js</summary>
<p>

```javascript

// Copy paste the below script in the console to give a visual gauge of events per second that are received over the websocket

var s;

function listenJob() {
  var jobid = $('#jobid').val();
  var xrftoken = readCookie('csrftoken');

  s.send(JSON.stringify({"groups":{"jobs":["status_changed","summary"],"job_events": [jobid,],"control":["limit_reached_1"]},"xrftoken": xrftoken}));
}

function appendHTML() {
  $('body').append('<div id="wsdebug_wrapper" style="position:fixed; bottom: 0; left: 0"><div id="wsdebug" width="100%" style="background-color: #ABBAEA; font-size: 48px;">Hello World</div><br><input id="jobid" type="text"><input id="dolisten" type="button" value="Submit" onclick="listenJob()"></div>')
}

$(document).ready(function()  {
  appendHTML();
  debugConnect();
});

function range_str(start, end) {
  var res = [];
  for (const x of Array(end-start).keys()) {
    res.push((start+x).toString());
  }
  return res;
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function debugConnect() {
  var buff = [];
  var buff_max = 1024;

  var saved_max = [[0,0,0], [0,0,0], [0,0,0]];

  var AVG_INDEX = 0;
  var STDEV_INDEX = 1;
  var MAX_INDEX = 2;

  s = new WebSocket("wss://" + window.location.hostname + ":" + window.location.port +"/websocket/");
  s.addEventListener('open', function (event) {
    console.log("Connected to debug websocket");
  });

  s.addEventListener('message', function (event) {
    var e = JSON.parse(event.data);
    if ('created' in e) {
      var now_seconds = Math.round(+new Date()/1000);
      var event_ts_seconds = Math.round(Date.parse(e['created'])/1000);
      var diff = now_seconds - event_ts_seconds;

      buff.push(diff)
      if (buff.length > buff_max) {
        buff.shift();
      }

      var res = buff_calc(buff);
      var avg = res[0];
      var stdev = res[1];
      var max = res[2];

      for (var i=0; i < 3; ++i) {
        var entry = saved_max[i];
        if (res[i] > entry[i]) {
          saved_max[i] = res;
        }
      }

      str = "<pre>\n";
      str += "Lag " + str_vals(res) + "\n";
      str += "MAX AVERAGE " + str_vals(saved_max[0]) + "\n";
      str += "MAX STDEV " + str_vals(saved_max[1]) + "\n";
      str += "MAX MAX " + str_vals(saved_max[2]) + "\n";
      str += "</pre>";

      $('#wsdebug').html(str);
    }
  });
}



function buff_calc(buff) {
  var total = 0;

  var max = 0;
  for (var i=0; i < buff.length; ++i) {
    total += buff[i];
    if (buff[i] > max) {
      max = buff[i];
    }
  }
  if (total == 0) {
    total = 1;
  }
  var avg = total / buff.length;

  total = 0;
  for (var i=0; i < buff.length; ++i) {
    var u = buff[i] - avg;
    var sq = u*u;
    total += sq;
  }
  if (total == 0) {
    total = 1;
  }

  var stdev = Math.sqrt(total / buff.length);

  return [avg, stdev, max];
}

function str_vals(c) {
  return "avg " + c[0].toString() + " stdev " + c[1].toString() + " max " + c[2].toString();
}
```

</p>
</details>
