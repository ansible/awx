var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Resize () {
    this.name = 'Resize';
}
inherits(_Resize, _State);
var Resize = new _Resize();
exports.Resize = Resize;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _CornerSelected () {
    this.name = 'CornerSelected';
}
inherits(_CornerSelected, _State);
var CornerSelected = new _CornerSelected();
exports.CornerSelected = CornerSelected;

function _Selected1 () {
    this.name = 'Selected1';
}
inherits(_Selected1, _State);
var Selected1 = new _Selected1();
exports.Selected1 = Selected1;

function _Selected3 () {
    this.name = 'Selected3';
}
inherits(_Selected3, _State);
var Selected3 = new _Selected3();
exports.Selected3 = Selected3;

function _Move () {
    this.name = 'Move';
}
inherits(_Move, _State);
var Move = new _Move();
exports.Move = Move;

function _Ready () {
    this.name = 'Ready';
}
inherits(_Ready, _State);
var Ready = new _Ready();
exports.Ready = Ready;

function _EditLabel () {
    this.name = 'EditLabel';
}
inherits(_EditLabel, _State);
var EditLabel = new _EditLabel();
exports.EditLabel = EditLabel;

function _Selected2 () {
    this.name = 'Selected2';
}
inherits(_Selected2, _State);
var Selected2 = new _Selected2();
exports.Selected2 = Selected2;




_Resize.prototype.onMouseUp = function (controller) {

    controller.changeState(CornerSelected);

};
_Resize.prototype.onMouseUp.transitions = ['CornerSelected'];



_Start.prototype.start = function () {

    //controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];



_CornerSelected.prototype.onMouseDown = function (controller) {

    controller.changeState(Resize);

};
_CornerSelected.prototype.onMouseDown.transitions = ['Resize'];

_CornerSelected.prototype.onMouseUp = function (controller) {

    controller.changeState(Ready);

};
_CornerSelected.prototype.onMouseUp.transitions = ['Ready'];



_Selected1.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Selected1.prototype.onMouseMove.transitions = ['Move'];

_Selected1.prototype.onMouseUp = function (controller) {

    controller.changeState(Selected2);

};
_Selected1.prototype.onMouseUp.transitions = ['Selected2'];



_Selected3.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Selected3.prototype.onMouseMove.transitions = ['Move'];

_Selected3.prototype.onMouseUp = function (controller) {

    controller.changeState(EditLabel);

};
_Selected3.prototype.onMouseUp.transitions = ['EditLabel'];



_Move.prototype.onMouseUp = function (controller) {

    controller.changeState(Selected2);

};
_Move.prototype.onMouseUp.transitions = ['Selected2'];



_Ready.prototype.onMouseDown = function (controller) {

    controller.changeState(Selected1);

    controller.changeState(CornerSelected);

};
_Ready.prototype.onMouseDown.transitions = ['Selected1', 'CornerSelected'];



_EditLabel.prototype.onMouseDown = function (controller) {

    controller.changeState(Ready);

};
_EditLabel.prototype.onMouseDown.transitions = ['Ready'];



_Selected2.prototype.onMouseDown = function (controller) {

    controller.changeState(Ready);

    controller.changeState(Selected3);

};
_Selected2.prototype.onMouseDown.transitions = ['Ready', 'Selected3'];


