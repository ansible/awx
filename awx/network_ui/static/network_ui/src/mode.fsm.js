var inherits = require('inherits');
var fsm = require('./fsm.js');
var move = require('./move.js');
var group = require('./group.js');

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

    controller.changeState(Rack);

};
_Start.prototype.start.transitions = ['MultiSite'];



_Interface.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Device);

    controller.next_controller.handle_message(msg_type, $event);

};
_Interface.prototype.onMouseWheel.transitions = ['Device'];

_Site.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.rack_toolbox.enabled = true;
};

_Site.prototype.end = function (controller) {

    controller.scope.rack_toolbox.enabled = false;
};


_Site.prototype.onMouseWheel = function (controller, msg_type, $event) {


    if (controller.scope.current_scale < 0.1) {
        controller.changeState(MultiSite);
    } else if (controller.scope.current_scale > 0.5) {
        controller.changeState(Rack);
    }

    controller.next_controller.handle_message(msg_type, $event);

};
_Site.prototype.onMouseWheel.transitions = ['MultiSite', 'Rack'];



_Process.prototype.onMouseWheel = function (controller, msg_type, $event) {

    controller.next_controller.handle_message(msg_type, $event);

    //controller.changeState(Device);

};
_Process.prototype.onMouseWheel.transitions = ['Device'];

_MultiSite.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.site_toolbox.enabled = true;
};

_MultiSite.prototype.end = function (controller) {

    controller.scope.site_toolbox.enabled = false;
};


_MultiSite.prototype.onMouseWheel = function (controller, msg_type, $event) {

    if (controller.scope.current_scale > 0.1) {
        controller.changeState(Site);
    }

    controller.next_controller.handle_message(msg_type, $event);
};
_MultiSite.prototype.onMouseWheel.transitions = ['Site'];

_Device.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.app_toolbox.enabled = true;
};

_Device.prototype.end = function (controller) {

    controller.scope.app_toolbox.enabled = false;
};

_Device.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Process);

    //controller.changeState(Interface);

    //controller.changeState(Site);

    if (controller.scope.current_scale < 5) {
        controller.changeState(Rack);
    }

    controller.next_controller.handle_message(msg_type, $event);
};
_Device.prototype.onMouseWheel.transitions = ['Process', 'Interface', 'Rack'];


_Rack.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
    controller.scope.inventory_toolbox.enabled = true;
    controller.scope.move_controller.changeState(move.Ready);
    controller.scope.group_controller.changeState(group.Ready);
};

_Rack.prototype.end = function (controller) {

    controller.scope.inventory_toolbox.enabled = false;
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

    controller.next_controller.handle_message(msg_type, $event);
};
_Rack.prototype.onMouseWheel.transitions = ['Site', 'Device'];

