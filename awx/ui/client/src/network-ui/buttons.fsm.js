/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Ready () {
    this.name = 'Ready';
}
inherits(_Ready, _State);
var Ready = new _Ready();
exports.Ready = Ready;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _ButtonPressed () {
    this.name = 'ButtonPressed';
}
inherits(_ButtonPressed, _State);
var ButtonPressed = new _ButtonPressed();
exports.ButtonPressed = ButtonPressed;




_Ready.prototype.onMouseDown = function (controller, msg_type, $event) {

    var i = 0;
    var buttons = controller.scope.all_buttons;
    var button = null;
    for (i = 0; i < buttons.length; i++) {
        button = buttons[i];
        if (button.is_selected(controller.scope.mouseX, controller.scope.mouseY)) {
            button.fsm.handle_message(msg_type, $event);
            controller.changeState(ButtonPressed);
            break;
        }
        button = null;
    }
    if (button === null) {
        controller.delegate_channel.send(msg_type, $event);
    }

};
_Ready.prototype.onMouseDown.transitions = ['ButtonPressed'];

_Ready.prototype.onMouseMove = function (controller, msg_type, $event) {

    if (!controller.scope.hide_buttons) {

        var i = 0;
        var buttons = controller.scope.all_buttons;
        var button = null;
        for (i = 0; i < buttons.length; i++) {
            button = buttons[i];
            button.mouse_over = false;
            if (button.is_selected(controller.scope.mouseX, controller.scope.mouseY)) {
                button.mouse_over = true;
            }
        }
    }

    controller.delegate_channel.send(msg_type, $event);
};


_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];



_ButtonPressed.prototype.onMouseUp = function (controller, msg_type, $event) {

    var i = 0;
    var buttons = controller.scope.all_buttons;
    var button = null;
    for (i = 0; i < buttons.length; i++) {
        button = buttons[i];
        button.fsm.handle_message(msg_type, $event);
    }
    controller.changeState(Ready);

};
_ButtonPressed.prototype.onMouseUp.transitions = ['Ready'];
