/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var move = require('./move.js');
var group = require('./group.js');
var rack_fsm = require('./rack.fsm.js');
var site_fsm = require('./site.fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Interface () {
    this.name = 'Interface';
}
inherits(_Interface, _State);
var Interface = new _Interface();
exports.Interface = Interface;

function _Site () {
    this.name = 'Site';
}
inherits(_Site, _State);
var Site = new _Site();
exports.Site = Site;

function _Process () {
    this.name = 'Process';
}
inherits(_Process, _State);
var Process = new _Process();
exports.Process = Process;

function _MultiSite () {
    this.name = 'MultiSite';
}
inherits(_MultiSite, _State);
var MultiSite = new _MultiSite();
exports.MultiSite = MultiSite;

function _Rack () {
    this.name = 'Rack';
}
inherits(_Rack, _State);
var Rack = new _Rack();
exports.Rack = Rack;

function _Device () {
    this.name = 'Device';
}
inherits(_Device, _State);
var Device = new _Device();
exports.Device = Device;


_State.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
};


_Start.prototype.start = function (controller) {

    controller.scope.app_toolbox_controller.handle_message('Disable', {});
    controller.scope.inventory_toolbox_controller.handle_message('Disable', {});
    controller.scope.rack_toolbox_controller.handle_message('Disable', {});
    controller.scope.site_toolbox_controller.handle_message('Disable', {});

    controller.changeState(Rack);
};
_Start.prototype.start.transitions = ['MultiSite'];



_Interface.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Device);

    controller.delegate_channel.send(msg_type, $event);

};
_Interface.prototype.onMouseWheel.transitions = ['Device'];

_Interface.prototype.onScaleChanged = _Interface.prototype.onMouseWheel;

_Site.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.rack_toolbox_controller.handle_message('Enable', {});
    controller.scope.rack_controller.changeState(rack_fsm.Ready);
};

_Site.prototype.end = function (controller) {

    controller.scope.rack_toolbox_controller.handle_message('Disable', {});
    controller.scope.rack_controller.changeState(rack_fsm.Disable);
};


_Site.prototype.onMouseWheel = function (controller, msg_type, $event) {


    if (controller.scope.current_scale < 0.1) {
        controller.changeState(MultiSite);
    } else if (controller.scope.current_scale > 0.5) {
        controller.changeState(Rack);
    }

    controller.delegate_channel.send(msg_type, $event);

};
_Site.prototype.onMouseWheel.transitions = ['MultiSite', 'Rack'];

_Site.prototype.onScaleChanged = _Site.prototype.onMouseWheel;


_Process.prototype.onMouseWheel = function (controller, msg_type, $event) {

    controller.delegate_channel.send(msg_type, $event);

    //controller.changeState(Device);

};
_Process.prototype.onMouseWheel.transitions = ['Device'];

_Process.prototype.onScaleChanged = _Process.prototype.onMouseWheel;

_MultiSite.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.site_toolbox_controller.handle_message('Enable', {});
    controller.scope.site_controller.changeState(site_fsm.Ready);
};

_MultiSite.prototype.end = function (controller) {

    controller.scope.site_toolbox_controller.handle_message('Disable', {});
    controller.scope.site_controller.changeState(site_fsm.Disable);
};


_MultiSite.prototype.onMouseWheel = function (controller, msg_type, $event) {

    if (controller.scope.current_scale > 0.1) {
        controller.changeState(Site);
    }

    controller.delegate_channel.send(msg_type, $event);
};
_MultiSite.prototype.onMouseWheel.transitions = ['Site'];

_MultiSite.prototype.onScaleChanged = _MultiSite.prototype.onMouseWheel;

_Device.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.app_toolbox_controller.handle_message('Enable', {});
};

_Device.prototype.end = function (controller) {

    controller.scope.app_toolbox_controller.handle_message('Disable', {});
};

_Device.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Process);

    //controller.changeState(Interface);

    //controller.changeState(Site);

    if (controller.scope.current_scale < 5) {
        controller.changeState(Rack);
    }

    controller.delegate_channel.send(msg_type, $event);
};
_Device.prototype.onMouseWheel.transitions = ['Process', 'Interface', 'Rack'];

_Device.prototype.onScaleChanged = _Device.prototype.onMouseWheel;

_Rack.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.inventory_toolbox_controller.handle_message('Enable', {});
    controller.scope.move_controller.changeState(move.Ready);
    controller.scope.group_controller.changeState(group.Ready);
};

_Rack.prototype.end = function (controller) {

    controller.scope.inventory_toolbox_controller.handle_message('Disable', {});
    controller.scope.move_controller.changeState(move.Disable);
    controller.scope.group_controller.changeState(group.Disable);
};

_Rack.prototype.onMouseWheel = function (controller, msg_type, $event) {

    if (controller.scope.current_scale < 0.5) {
        controller.changeState(Site);
    }

    if (controller.scope.current_scale > 5) {
        controller.changeState(Device);
    }

    controller.delegate_channel.send(msg_type, $event);
};
_Rack.prototype.onMouseWheel.transitions = ['Site', 'Device'];

_Rack.prototype.onScaleChanged = _Rack.prototype.onMouseWheel;
