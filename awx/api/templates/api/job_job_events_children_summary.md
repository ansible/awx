# View a summary of children events

Special view to facilitate processing job output in the UI.
In order to collapse events and their children, the UI needs to know how
many children exist for a given event.
The UI also needs to know the order of the event (0 based index), which
usually matches the counter, but not always.
This view returns a JSON object where the key is the event counter, and the value
includes the number of children (and grandchildren) events.
Only events with children are included in the output.

## Example

e.g. Demo Job Template job
tuple(event counter, uuid, parent_uuid)

```
(1, '4598d19e-93b4-4e33-a0ae-b387a7348964', '')
(2, 'aae0d189-e3cb-102a-9f00-000000000006', '4598d19e-93b4-4e33-a0ae-b387a7348964')
(3, 'aae0d189-e3cb-102a-9f00-00000000000c', 'aae0d189-e3cb-102a-9f00-000000000006')
(4, 'f4194f14-e406-4124-8519-0fdb08b18f4b', 'aae0d189-e3cb-102a-9f00-00000000000c')
(5, '39f7ad99-dbf3-41e0-93f8-9999db4004f2', 'aae0d189-e3cb-102a-9f00-00000000000c')
(6, 'aae0d189-e3cb-102a-9f00-000000000008', 'aae0d189-e3cb-102a-9f00-000000000006')
(7, '39a49992-5ca4-4b6c-b178-e56d0b0333da', 'aae0d189-e3cb-102a-9f00-000000000008')
(8, '504f3b28-3ea8-4f6f-bd82-60cf8e807cc0', 'aae0d189-e3cb-102a-9f00-000000000008')
(9, 'a242be54-ebe6-4021-afab-f2878bff2e9f', '4598d19e-93b4-4e33-a0ae-b387a7348964')
```

output

```
{
"1": {
    "rowNumber": 0,
    "numChildren": 8
},
"2": {
    "rowNumber": 1,
    "numChildren": 6
},
"3": {
    "rowNumber": 2,
    "numChildren": 2
},
"6": {
    "rowNumber": 5,
    "numChildren": 2
}
}
"meta_event_nested_parent_uuid": {}
}
```

counter 1 is event 0, and has 8 children
counter 2 is event 1, and has 6 children
etc.

The UI also needs to be able to collapse over "meta" events -- events that
show up due to verbosity or warnings from the system while the play is running.
These events have a 0 level event, with no parent uuid.

```
playbook_on_start
verbose
  playbook_on_play_start
    playbook_on_task_start
      runner_on_start        <- level 3
verbose                      <- jump to level 0
verbose
        runner_on_ok         <- jump back to level 3
      playbook_on_task_start
        runner_on_start
        runner_on_ok
verbose
verbose
      playbook_on_stats
```

These verbose statements that fall in the middle of a series of children events
are problematic for the UI.
To help, this view will attempt to place the events into the hierarchy, without
the event level jumps.

```
playbook_on_start
  verbose
  playbook_on_play_start
    playbook_on_task_start
      runner_on_start        <- A
        verbose              <- this maps to the uuid of A
        verbose
        runner_on_ok
      playbook_on_task_start <- B
        runner_on_start
        runner_on_ok
        verbose              <- this maps to the uuid of B
        verbose
      playbook_on_stats
```

The output will include a JSON object where the key is the event counter,
and the value is the assigned nested uuid.
