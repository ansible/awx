var inherits = require('inherits');
var fsm = require('./fsm.js');
var messages = require('./messages.js');
var models = require('./models.js');

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




_Disabled.prototype.onEnableTest = function (controller) {

    controller.changeState(Ready);
};
_Disabled.prototype.onEnableTest.transitions = ['Ready'];



_Start.prototype.start = function (controller) {

    controller.changeState(Disabled);

};
_Start.prototype.start.transitions = ['Disabled'];



_Running.prototype.onTestCompleted = function (controller) {

    controller.changeState(Reporting);
};
_Running.prototype.onTestCompleted.transitions = ['Reporting'];

_Reporting.prototype.start = function (controller) {

    controller.scope.replay = false;
    controller.scope.disconnected = false;
    controller.scope.recording = false;
    controller.scope.test_results.push(new models.TestResult(controller.scope.current_test.name, "passed"));
    controller.changeState(Ready);
};
_Reporting.prototype.start.transitions = ['Ready'];


_Loading.prototype.start = function (controller) {

    if (controller.scope.current_tests.length === 0) {
        controller.changeState(Disabled);
    } else {
        console.log("Starting test");
        controller.scope.current_test = controller.scope.current_tests.shift();
        controller.scope.onSnapshot(controller.scope.current_test.pre_test_snapshot);
        controller.scope.replay = true;
        controller.scope.disconnected = true;
        controller.scope.test_events = controller.scope.current_test.event_trace.slice();
        controller.scope.test_events.push(new messages.TestCompleted());
        controller.changeState(Running);
    }
};
_Loading.prototype.start.transitions = ['Running'];



_Ready.prototype.onDisableTest = function (controller) {

    controller.changeState(Disabled);
};
_Ready.prototype.onDisableTest.transitions = ['Disabled'];

_Ready.prototype.start = function (controller) {

    controller.changeState(Loading);
};
_Ready.prototype.start.transitions = ['Loading'];



_Reporting.prototype.onTestReported = function (controller) {

    controller.changeState(Ready);

};
_Reporting.prototype.onTestReported.transitions = ['Ready'];

