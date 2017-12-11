
Finite State Machine Designs
============================

This directory contains the finite state machine designs that were used to
generate the skeleton of the javascript implementations and can be used to
check that the implementations still match the designs.


**Machine Readable FSM Schema**

The machine readable FSM schema contains three top-level elements: `name`, `states`, and `transitions`.
The `name` element is a string.
The `states` element contains a list of `state` elements which have attributes `id`, `label`, and `x`, and `y`.
The `transitions` element contains a list of `transition` elements which have attributes `from_state`,
`to_state`, and `label`.


**Design Diagrams**

The diagrams below are visual representations of the finite state machine designs in this directory.
The equivalent machine readable representations are linked as well.

**Null FSM**
* See: null.yml

![Null FSM](null.png)

**Button FSM**
* See: button.yml

![Button FSM](button.png)

**Buttons FSM**
* See: buttons.yml

![Buttons FSM](buttons.png)

**Device Detail FSM**
* See: device_detail.yml

![Device Detail FSM](device_detail.png)

**Group FSM**
* See: group.yml

![Group FSM](group.png)

**Hot Keys FSM**
* See: hotkeys.yml

![Hot Keys FSm](hotkeys.png)

**Link FSM**
* See: link.yml

![Link](link.png)

**Mode FSM**
* See: mode.yml

![Mode](mode.png)

**Move FSM**
* See: move.yml

![Move](move.png)

**Rack FSM**
* See: rack.yml

![Rack](rack.png)

**Site FSM**
* See: site.yml

![Site](site.png)

**Stream FSM**
* See: stream.yml

![Stream](stream.png)

**Time FSM**
* See: time.yml

![Time](time.png)

**Toolbox FSM**
* See: toolbox.yml

![Toolbox](toolbox.png)

**View FSM**
* See: view.yml

![View](view.png)
