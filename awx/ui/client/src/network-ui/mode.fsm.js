/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var move = require('./move.fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Rack () {
    this.name = 'Rack';
}
inherits(_Rack, _State);
var Rack = new _Rack();
exports.Rack = Rack;


_State.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
};


_Start.prototype.start = function (controller) {

    controller.scope.inventory_toolbox_controller.handle_message('Disable', {});

    controller.changeState(Rack);
};
_Start.prototype.start.transitions = ['MultiSite'];


_Rack.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.inventory_toolbox_controller.handle_message('Enable', {});
    controller.scope.move_controller.changeState(move.Ready);
};

_Rack.prototype.end = function (controller) {

    controller.scope.inventory_toolbox_controller.handle_message('Disable', {});
    controller.scope.move_controller.changeState(move.Disable);
};

