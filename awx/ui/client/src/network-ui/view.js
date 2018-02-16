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

function _Scale () {
    this.name = 'Scale';
}
inherits(_Scale, _State);
var Scale = new _Scale();
exports.Scale = Scale;

function _Pressed () {
    this.name = 'Pressed';
}
inherits(_Pressed, _State);
var Pressed = new _Pressed();
exports.Pressed = Pressed;

function _Pan () {
    this.name = 'Pan';
}
inherits(_Pan, _State);
var Pan = new _Pan();
exports.Pan = Pan;




_Ready.prototype.onMouseDown = function (controller) {

    controller.scope.pressedX = controller.scope.mouseX;
    controller.scope.pressedY = controller.scope.mouseY;
    controller.scope.lastPanX = controller.scope.panX;
    controller.scope.lastPanY = controller.scope.panY;
    controller.scope.closeDetailsPanel();
    controller.changeState(Pressed);

};
_Ready.prototype.onMouseDown.transitions = ['Pressed'];

_Ready.prototype.onMouseWheel = function (controller, msg_type, $event) {

    controller.changeState(Scale);
    controller.handle_message(msg_type, $event);
};
_Ready.prototype.onMouseWheel.transitions = ['Scale'];


_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];

_Scale.prototype.onMouseWheel = function (controller, msg_type, message) {
      var delta = message[1];
      var new_scale = Math.max(0.001, Math.min(100, (controller.scope.current_scale + delta / (100 / controller.scope.current_scale))));
      var new_panX = controller.scope.mouseX - new_scale * ((controller.scope.mouseX - controller.scope.panX) / controller.scope.current_scale);
      var new_panY = controller.scope.mouseY - new_scale * ((controller.scope.mouseY - controller.scope.panY) / controller.scope.current_scale);
      controller.scope.updateScaledXY();
      controller.scope.current_scale = new_scale;
      controller.scope.panX = new_panX;
      controller.scope.panY = new_panY;
      var item = controller.scope.context_menus[0];
      item.enabled = false;
      controller.scope.$emit('awxNet-UpdateZoomWidget', controller.scope.current_scale, true);
      controller.scope.updatePanAndScale();
      controller.changeState(Ready);
};
_Scale.prototype.onMouseWheel.transitions = ['Ready'];


_Pressed.prototype.onMouseUp = function (controller) {

    controller.changeState(Ready);

};
_Pressed.prototype.onMouseUp.transitions = ['Ready'];

_Pressed.prototype.onMouseMove = function (controller, msg_type, $event) {

    controller.changeState(Pan);
    controller.handle_message(msg_type, $event);
};
_Pressed.prototype.onMouseMove.transitions = ['Pan'];

_Pan.prototype.onMouseMove = function (controller) {

    controller.scope.panX = (controller.scope.mouseX - controller.scope.pressedX) + controller.scope.lastPanX;
    controller.scope.panY = (controller.scope.mouseY - controller.scope.pressedY) + controller.scope.lastPanY;
    controller.scope.updateScaledXY();
    controller.scope.updatePanAndScale();
};

_Pan.prototype.onMouseUp = function (controller) {

    controller.changeState(Ready);

};
_Pan.prototype.onMouseUp.transitions = ['Ready'];
