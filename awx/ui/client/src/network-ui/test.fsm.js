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

    var test_result = null;
    controller.scope.replay = false;
    controller.scope.disconnected = false;
    controller.scope.recording = false;
    var result = "passed";
    if (controller.scope.test_errors.length > 0) {
        result = "errored";
    }
    test_result = new models.TestResult(controller.scope.test_result_id_seq(),
                                        controller.scope.current_test.name,
                                        result,
                                        new Date().toISOString(),
                                        controller.scope.version);
    controller.scope.test_results.push(test_result);
    console.log(["Reporting test", test_result.name, test_result.id]);
    controller.scope.send_control_message(new messages.TestResult(controller.scope.client_id,
                                                                  test_result.id,
                                                                  test_result.name,
                                                                  test_result.result,
                                                                  test_result.date,
                                                                  test_result.code_under_test));
    if (typeof(window.__coverage__) !== "undefined" && window.__coverage__ !== null) {
        console.log(["Reporting coverage", test_result.name, test_result.id]);
        controller.scope.send_control_message(new messages.Coverage(controller.scope.client_id, window.__coverage__, test_result.id));
    }
    controller.changeState(Loading);
};
_Reporting.prototype.start.transitions = ['Loading'];


_Loading.prototype.start = function (controller) {

    if (controller.scope.current_tests.length === 0) {
        controller.changeState(Disabled);
    } else {
        console.log("Starting test");
        controller.scope.current_test = controller.scope.current_tests.shift();
        controller.scope.onSnapshot(controller.scope.current_test.pre_test_snapshot);
        controller.scope.replay = true;
        controller.scope.disconnected = true;
        controller.scope.test_errors = [];
        controller.scope.test_events = controller.scope.current_test.event_trace.slice();
        controller.scope.test_events.push(new messages.TestCompleted());
        controller.scope.reset_coverage();
        controller.scope.reset_flags();
        controller.scope.reset_fsm_state();
        controller.scope.reset_history();
        controller.scope.reset_toolboxes();
        controller.changeState(Running);
    }
};
_Loading.prototype.start.transitions = ['Running'];



_Ready.prototype.onDisableTest = function (controller) {

    controller.changeState(Disabled);
};
_Ready.prototype.onDisableTest.transitions = ['Disabled'];

_Ready.prototype.start = function (controller) {

    var load_id = controller.scope.test_result_id_seq();

    console.log(["Reporting Load", load_id]);
    controller.scope.send_control_message(new messages.TestResult(controller.scope.client_id,
                                                                  load_id,
                                                                  "Load",
                                                                  "passed",
                                                                  new Date().toISOString(),
                                                                  controller.scope.version));
    if (typeof(window.__coverage__) !== "undefined" && window.__coverage__ !== null) {
        console.log(["Reporting Load Coverage", load_id]);
        controller.scope.send_control_message(new messages.Coverage(controller.scope.client_id, window.__coverage__, load_id));
    }

    controller.changeState(Loading);
};
_Ready.prototype.start.transitions = ['Loading'];
