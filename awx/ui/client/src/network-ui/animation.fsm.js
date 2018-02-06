/* Copyright (c) 2018  Benjamin Thomasson */
/* Copyright (c) 2018 Red Hat, Inc. */

var inherits = require('inherits');
var fsm = require('./fsm.js');


function _Start () {
    this.name = 'Start';
}
inherits(_Start, fsm._State);
var Start = new _Start();
exports.Start = Start;

function _Completed () {
    this.name = 'Completed';
}
inherits(_Completed, fsm._State);
var Completed = new _Completed();
exports.Completed = Completed;

function _Cancelled () {
    this.name = 'Cancelled';
}
inherits(_Cancelled, fsm._State);
var Cancelled = new _Cancelled();
exports.Cancelled = Cancelled;

function _Running () {
    this.name = 'Running';
}
inherits(_Running, fsm._State);
var Running = new _Running();
exports.Running = Running;


_Start.prototype.start = function (controller) {

    controller.changeState(Running);
};
_Start.prototype.start.transitions = ['Running'];

_Running.prototype.start = function (controller) {

    controller.scope.interval = setInterval(function () {
        controller.scope.frame_number = controller.scope.frame_number_seq();
        if (!controller.scope.active) {
            return;
        }
        if (controller.scope.frame_number > controller.scope.steps) {
            controller.scope.fsm.handle_message('AnimationCompleted');
            return;
        }
        controller.scope.callback(controller.scope);
        controller.scope.scope.$apply();
    }, 17);
};

_Running.prototype.onAnimationCancelled = function (controller) {

    controller.changeState(Cancelled);

};
_Running.prototype.onAnimationCancelled.transitions = ['Cancelled'];

_Running.prototype.onAnimationCompleted = function (controller) {

    controller.changeState(Completed);

};
_Running.prototype.onAnimationCompleted.transitions = ['Completed'];

_Completed.prototype.start = function (controller) {
    controller.scope.active = false;
    clearInterval(controller.scope.interval);
};

_Cancelled.prototype.start = function (controller) {
    controller.scope.active = false;
    clearInterval(controller.scope.interval);
};
