

.PHONY: check extract

FSMS = time test mode buttons button toolbox site


extract:
	mkdir -p extracted
	./extract.js ./time.js > extracted/time.yml
	./extract.js ./test.fsm.js > extracted/test.yml
	./extract.js ./mode.fsm.js > extracted/mode.yml
	./extract.js ./buttons.js > extracted/buttons.yml
	./extract.js ./button.js > extracted/button.yml
	./extract.js ./toolbox.fsm.js > extracted/toolbox.yml
	./extract.js ./site.fsm.js > extracted/site.yml
	./extract.js ./rack.fsm.js > extracted/rack.yml
	./extract.js ./group.js > extracted/group.yml
	./extract.js ./stream.fsm.js > extracted/stream.yml
	./extract.js ./link.js > extracted/link.yml
	./extract.js ./details.panel.fsm.js > extracted/details_panel.yml
	./extract.js ./move.js > extracted/move.yml
	./extract.js ./device.detail.fsm.js > extracted/device_detail.yml
	./extract.js ./view.js > extracted/view.yml
	./extract.js ./keybindings.fsm.js > extracted/keybindings.yml
	./extract.js ./hotkeys.fsm.js > extracted/hotkeys.yml
	./extract.js ./null.fsm.js > extracted/null.yml


check: extract
	./tools/fsm-diff ../../../../network_ui/designs/time.yml extracted/time.yml
	./tools/fsm-diff ../../../../network_ui/designs/test.yml extracted/test.yml
	./tools/fsm-diff ../../../../network_ui/designs/mode.yml extracted/mode.yml
	./tools/fsm-diff ../../../../network_ui/designs/buttons.yml extracted/buttons.yml
	./tools/fsm-diff ../../../../network_ui/designs/button.yml extracted/button.yml
	./tools/fsm-diff ../../../../network_ui/designs/toolbox.yml extracted/toolbox.yml
	./tools/fsm-diff ../../../../network_ui/designs/site.yml extracted/site.yml
	./tools/fsm-diff ../../../../network_ui/designs/rack.yml extracted/rack.yml
	./tools/fsm-diff ../../../../network_ui/designs/group.yml extracted/group.yml
	./tools/fsm-diff ../../../../network_ui/designs/stream.yml extracted/stream.yml

