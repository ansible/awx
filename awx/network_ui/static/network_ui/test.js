var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Disabled () {
    this.name = 'Disabled';
}
inherits(_Disabled, _State);
var Disabled = new _Disabled();
exports.Disabled = Disabled;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Running () {
    this.name = 'Running';
}
inherits(_Running, _State);
var Running = new _Running();
exports.Running = Running;

function _Loading () {
    this.name = 'Loading';
}
inherits(_Loading, _State);
var Loading = new _Loading();
exports.Loading = Loading;

function _Ready () {
    this.name = 'Ready';
}
inherits(_Ready, _State);
var Ready = new _Ready();
exports.Ready = Ready;

function _Reporting () {
    this.name = 'Reporting';
}
inherits(_Reporting, _State);
var Reporting = new _Reporting();
exports.Reporting = Reporting;




_Disabled.prototype.onEnable = function (controller) {

    controller.changeState(Ready);

};
_Disabled.prototype.onEnable.transitions = ['Ready'];



_Start.prototype.start = function (controller) {

    controller.changeState(Disabled);

};
_Start.prototype.start.transitions = ['Disabled'];



_Running.prototype.onTestCompleted = function (controller) {

    controller.changeState(Reporting);

};
_Running.prototype.onTestCompleted.transitions = ['Reporting'];



_Loading.prototype.onTestLoaded = function (controller) {

    controller.changeState(Running);

};
_Loading.prototype.onTestLoaded.transitions = ['Running'];



_Ready.prototype.onDisable = function (controller) {

    controller.changeState(Disabled);

};
_Ready.prototype.onDisable.transitions = ['Disabled'];

_Ready.prototype.onStartTest = function (controller) {

    controller.changeState(Loading);

};
_Ready.prototype.onStartTest.transitions = ['Loading'];



_Reporting.prototype.onTestReported = function (controller) {

    controller.changeState(Ready);

};
_Reporting.prototype.onTestReported.transitions = ['Ready'];

