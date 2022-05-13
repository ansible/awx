# Subsystem Metrics

The subsystem metrics offers a flexible way to collect and aggregate metrics across the application and display them at the `api/v2/metrics` endpoint.

```python
m = Metrics() # initialize the metrics object
m.inc("foo", 1) # increment a value
m.pipe_execute() # save the values to Redis
```

## Endpoint reflects Redis

The endpoint reflects whatever values are in Redis. The metrics are stored in a Redis hash set called `awx_metrics`, and each metric is a field in this hash set. When a POST or GET is made to the endpoint, the view will load the data stored in Redis, format it to be Prometheus-compatible, and return it as a response. You can view the metrics in Redis by connecting to an instance via a client.

```
redis /run/redis/redis.sock> hget awx_metrics callback_receiver_events_insert_db
"100"
```

Each control node tracks its own metrics. Thus, there will be a `callback_receiver_events_insert_db` metric for each instance in the cluster.

## Metrics class

`subsystem_metrics.Metrics` is a class that can access, track, and update the Redis metrics. It is the interface between the python code and the Redis instance that ultimately stores the metrics. Different parts of the application are expected to initialize their own `Metrics` object and use it to interface with Redis.

## Performance consideration

Saving to Redis can be expensive if called too frequently, i.e. called rapidly in a while loop.

As such, the subsystem metrics is designed to track and aggregate data in-memory, and only update to Redis periodically. Because the endpoint only reflects what is in Redis, there could be a delay between the moment the measurement is taken and when that measurement is displayed at the endpoint.

The `inc` and `set` commands only affect the in-memory values, and calling `pipe_execute` updates the corresponding metrics in Redis. The trade-off with this design is real-time accuracy of the measurements reported at the `api/v2/metrics` endpoint. Keep in mind that this endpoint is likely to be scraped at an interval of 5-15 seconds from Prometheus.Therefore having a system that reports metrics at a resolution of < 1 second is not necessary.

## Thread safety

The Metrics object is not thread safe. Each thread should initialize and use its own `Metrics` object. `set` and `inc` will update a basic python int object without using any sort of mutex or lock. As such, multiple threads accessing and updating this value could lead to inaccuracies and race conditions.

However, from the perspective of Redis, `pipe_execute` *is* thread safe. So multiple `Metrics` objects can track and increment the same metric across threads and processes.

```
                                                     In memory
          Thread 1  +-------------+                 +---------+
                    |             |  inc("foo", 1)  |         |
        +---------->|  Metrics A  | --------------->|  IntM() +-----------------+
        |           |             |                 |         |   pipe_execute  |
        |           +-------------+                 +---------+                 |
        |                                                                   +---v---+
Process                                                                     |       |
                                                                            | Redis |
        |                                                                   |       |
        |                                            In memory              +---^---+
        |           +-------------+                 +---------+                 |
        | Thread 2  |             |  inc("foo", 1)  |         |                 |
        +---------->|  Metrics B  | --------------->|  IntM() +-----------------+
                    |             |                 |         |   pipe_execute
                    +-------------+                 +---------+
```

## When to call pipe_execute

As mentioned, it is best practice to ensure `pipe_execute` is not called too frequently. For convenience, the `should_pipe_execute` method can be used to determine whether enough time has elapsed since the last `pipe_execute` to warrant a new call. This interval is determined by the `SUBSYSTEM_METRICS_INTERVAL_SAVE_TO_REDIS` setting.

```python
m = Metrics()
while True:
    m.inc("foo", 1)
    if m.should_pipe_execute():
        m.pipe_execute()
    if some_condition:
        break
m.pipe_execute()
```

Although the metric `foo` is being incremented very frequently in-memory, the metrics won't save to Redis each iteration of the while loop. Instead, it will only save to Redis if `should_pipe_execute` is `True`.

In the example above, once `some_condition` hits, there may still be values accrued in the `Metrics` object that still haven't been saved to Redis. Therefore a final `pipe_execute` is needed to ensure all values are updated in Redis.

## Metric types

#### Metrics intended to increment over time

* `IntM` - data that can be represented by an integer (whole number). e.g. number of events inserted into database
* `FloatM` - data that can be represented by a float, e.g. time it took to insert events into database

The above metrics are designed to increment (increase) the values in Redis. That is, calling `pipe_execute` will *add* the value currently stored in-memory to the value stored in Redis.

Note, to decrease a value, you can increment by a negative number, e.g. `inc("foo", -1)`

#### Metrics intended to override the previous value

* `SetIntM` - e.g. number of events in the Redis queue right now
* `SetFloatM` - e.g. time it took to execute the last task manager

The above metrics are designed to override whatever values are in Redis. Calling `pipe_execute` will *set* (and override) the value currently stored in-memory to the value stored in Redis.

#### Observing data that falls into buckets

* `HistogramM` - observations of a measurement across time that falls into pre-defined buckets

Example, the following metric captures how many events are batch-inserted into the database.

```
callback_receiver_batch_events_insert_db_bucket{le="10",node="awx_1"} 1
callback_receiver_batch_events_insert_db_bucket{le="50",node="awx_1"} 5
callback_receiver_batch_events_insert_db_bucket{le="150",node="awx_1"} 5
callback_receiver_batch_events_insert_db_bucket{le="350",node="awx_1"} 5
callback_receiver_batch_events_insert_db_bucket{le="650",node="awx_1"} 5
callback_receiver_batch_events_insert_db_bucket{le="2000",node="awx_1"} 5
callback_receiver_batch_events_insert_db_bucket{le="+Inf",node="awx_1"} 5
callback_receiver_batch_events_insert_db_count{node="awx_1"} 5
callback_receiver_batch_events_insert_db_sum{node="awx_1"} 5
```

The histogram is cumulative, meaning each successive bucket includes the values in the *preceding* bucket. In the above, one occurrence of the insertion process resulted in less than 10 events being inserted into the database. Four (5-1) occurrences resulted in between 10 and 50 events being inserted into the database.

## Metrics broadcast

Periodically, the `Metrics` object will broadcast the full metrics dataset to other control nodes in the cluster. This ensures that the metrics endpoint has data from all instances, not just the instance that the browser happens to be connected to at that moment.

This data received from other metrics is stored in Redis as a JSON string. For example, in a cluster with three control nodes, each Redis instance will contain the following keys.

```
awx_metrics_instance_awx_1
awx_metrics_instance_awx_2
awx_metrics_instance_awx_3
```

The `api/v2/metrics` endpoint will load the data from each of these instances, format it into Prometheus, and return it as a response.
