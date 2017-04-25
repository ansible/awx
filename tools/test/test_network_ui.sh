#!/bin/bash -x
TS="0.01"
./manage.py ui_test --verbose --time-scale 0.1
./manage.py replay_recording 143 recordings/test_create_two_switches.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_edit_labels2.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_undo_redo.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_undo_redo_control_mouse_wheel.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_deploy_destroy.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_undo_redo_create_destroy.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_multiple_viewers.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_view_hotkeys.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_recording.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_mouse.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_rack.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_link_unconnected.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_touches.replay --time-scale ${TS} --delete-topology-at-start
./manage.py replay_recording 143 recordings/test_export.replay --delete-topology-at-start --time-scale 0.1
./manage.py replay_recording 143 recordings/test_mouse_exit_enter.replay --delete-topology-at-start --time-scale ${TS}
sleep 1
istanbul report --root coverage --dir out text text-summary html
