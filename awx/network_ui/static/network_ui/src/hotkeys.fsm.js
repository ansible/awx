var inherits = require('inherits');
var fsm = require('./fsm.js');
var messages = require('./messages.js');

function _State () {
}
inherits(_State, fsm._State);


function _Enabled () {
    this.name = 'Enabled';
}
inherits(_Enabled, _State);
var Enabled = new _Enabled();
exports.Enabled = Enabled;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Disabled () {
    this.name = 'Disabled';
}
inherits(_Disabled, _State);
var Disabled = new _Disabled();
exports.Disabled = Disabled;




_Enabled.prototype.onDisable = function (controller) {

    controller.changeState(Disabled);

};
_Enabled.prototype.onDisable.transitions = ['Disabled'];


_Enabled.prototype.onKeyDown = function(controller, msg_type, $event) {

	var scope = controller.scope;

    if ($event.key === 'c' && ($event.ctrlKey || $event.metaKey)) {
        scope.first_controller.handle_message("CopySelected", $event);
    }

    if ($event.key === 'l') {
        scope.first_controller.handle_message("NewLink", $event);
        return;
    }

    if ($event.key === 'd') {
        scope.debug.hidden = !scope.debug.hidden;
        return;
    }
    if ($event.key === 'p') {
        scope.cursor.hidden = !scope.cursor.hidden;
        return;
    }
    if ($event.key === 'b') {
        scope.hide_buttons = !scope.hide_buttons;
        return;
    }
    if ($event.key === 'i') {
        scope.hide_interfaces = !scope.hide_interfaces;
        return;
    }

	if ($event.key === 'r') {
        scope.first_controller.handle_message("NewDevice", new messages.NewDevice("router"));
        return;
	}
    else if ($event.key === 's') {
        scope.first_controller.handle_message("NewDevice", new messages.NewDevice("switch"));
        return;
	}
    else if ($event.key === 'a') {
        scope.first_controller.handle_message("NewGroup", new messages.NewGroup("rack"));
        return;
	}
    else if ($event.key === 'h') {
        scope.first_controller.handle_message("NewDevice", new messages.NewDevice("host"));
        return;
	}
    else if ($event.key === 'g') {
        scope.first_controller.handle_message("NewGroup", new messages.NewGroup("group"));
        return;
	}
    else if ($event.key === 'e') {
        scope.first_controller.handle_message("NewGroup", new messages.NewGroup("site"));
        return;
	}
    else if ($event.key === '0') {
        scope.panX = 0;
        scope.panY = 0;
        scope.current_scale = 1.0;
        scope.updateScaledXY();
        scope.updatePanAndScale();
    }

	controller.next_controller.handle_message(msg_type, $event);
};

_Start.prototype.start = function (controller) {

    controller.changeState(Enabled);

};
_Start.prototype.start.transitions = ['Enabled'];



_Disabled.prototype.onEnable = function (controller) {

    controller.changeState(Enabled);

};
_Disabled.prototype.onEnable.transitions = ['Enabled'];


