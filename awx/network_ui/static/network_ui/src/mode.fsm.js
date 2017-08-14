var inherits = require('inherits');
var fsm = require('./fsm.js');

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

    controller.changeState(MultiSite);

};
_Start.prototype.start.transitions = ['MultiSite'];



_Interface.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Device);

    controller.next_controller.handle_message(msg_type, $event);

};
_Interface.prototype.onMouseWheel.transitions = ['Device'];


_Site.prototype.onMouseWheel = function (controller, msg_type, $event) {


    if (controller.scope.current_scale < 0.3) {
        controller.changeState(MultiSite);
    } else if (controller.scope.current_scale > 5) {
        controller.changeState(Device);
    }

    controller.next_controller.handle_message(msg_type, $event);

};
_Site.prototype.onMouseWheel.transitions = ['MultiSite', 'Device'];



_Process.prototype.onMouseWheel = function (controller, msg_type, $event) {

    controller.next_controller.handle_message(msg_type, $event);

    //controller.changeState(Device);

};
_Process.prototype.onMouseWheel.transitions = ['Device'];

_MultiSite.prototype.start = function (controller) {
    controller.scope.current_mode = controller.state.name;
};


_MultiSite.prototype.onMouseWheel = function (controller, msg_type, $event) {

    if (controller.scope.current_scale > 0.3) {
        controller.changeState(Site);
    }

    controller.next_controller.handle_message(msg_type, $event);
};
_MultiSite.prototype.onMouseWheel.transitions = ['Site'];



_Device.prototype.onMouseWheel = function (controller, msg_type, $event) {

    //controller.changeState(Process);

    //controller.changeState(Interface);

    //controller.changeState(Site);

    if (controller.scope.current_scale < 5) {
        controller.changeState(Site);
    }

    controller.next_controller.handle_message(msg_type, $event);
};
_Device.prototype.onMouseWheel.transitions = ['Process', 'Interface', 'Site'];


