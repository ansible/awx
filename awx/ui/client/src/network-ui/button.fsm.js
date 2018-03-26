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

function _Clicked () {
    this.name = 'Clicked';
}
inherits(_Clicked, _State);
var Clicked = new _Clicked();
exports.Clicked = Clicked;

function _Pressed () {
    this.name = 'Pressed';
}
inherits(_Pressed, _State);
var Pressed = new _Pressed();
exports.Pressed = Pressed;
function _Disabled () {
    this.name = 'Disabled';
}
inherits(_Disabled, _State);
var Disabled = new _Disabled();
exports.Disabled = Disabled;



// Begin ready state
_Ready.prototype.onMouseDown = function (controller) {

    controller.changeState(Pressed);

};
_Ready.prototype.onMouseDown.transitions = ['Pressed'];

_Ready.prototype.start = function (controller) {

    controller.scope.enabled = true;

};

_Ready.prototype.onDisable = function (controller) {

    controller.changeState(Disabled);

};
_Ready.prototype.onDisable.transitions = ['Disabled'];
// end ready state


_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Clicked.prototype.start = function (controller) {

    controller.scope.is_pressed = false;
    controller.changeState(Ready);
    controller.scope.callback(controller.scope);
};
_Clicked.prototype.start.transitions = ['Ready'];


_Pressed.prototype.start = function (controller) {
    controller.scope.is_pressed = true;
};

_Pressed.prototype.onMouseUp = function (controller) {

    controller.changeState(Clicked);

};
_Pressed.prototype.onMouseUp.transitions = ['Clicked'];

_Disabled.prototype.onEnable = function (controller) {

    controller.changeState(Ready);

};
_Disabled.prototype.onEnable.transitions = ['Ready'];

_Disabled.prototype.start = function (controller) {

    controller.scope.enabled = false;

};
