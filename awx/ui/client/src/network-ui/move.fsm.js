/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var models = require('./models.js');
var messages = require('./messages.js');
var util = require('./util.js');

function _State () {
}
inherits(_State, fsm._State);

function _Ready () {
    this.name = 'Ready';
}
inherits(_Ready, _State);
var Ready = new _Ready();
exports.Ready = Ready;

function _Disable () {
    this.name = 'Disable';
}
inherits(_Disable, _State);
var Disable = new _Disable();
exports.Disable = Disable;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Selected2 () {
    this.name = 'Selected2';
}
inherits(_Selected2, _State);
var Selected2 = new _Selected2();
exports.Selected2 = Selected2;

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

function _Selected1 () {
    this.name = 'Selected1';
}
inherits(_Selected1, _State);
var Selected1 = new _Selected1();
exports.Selected1 = Selected1;

function _Placing () {
    this.name = 'Placing';
}
inherits(_Placing, _State);
var Placing = new _Placing();
exports.Placing = Placing;


function _ContextMenu () {
    this.name = 'ContextMenu';
}
inherits(_ContextMenu, _State);
var ContextMenu = new _ContextMenu();
exports.ContextMenu = ContextMenu;


_State.prototype.onUnselectAll = function (controller, msg_type, $event) {

    controller.changeState(Ready);
    controller.delegate_channel.send(msg_type, $event);
};

_Ready.prototype.onPasteDevice = function (controller, msg_type, message) {

	var scope = controller.scope;
    var device = null;
    var remote_device = null;
    var intf = null;
    var link = null;
    var new_link = null;
    var i = 0;
    var c_messages = [];

    scope.pressedX = scope.mouseX;
    scope.pressedY = scope.mouseY;
    scope.pressedScaledX = scope.scaledX;
    scope.pressedScaledY = scope.scaledY;

    device = new models.Device(controller.scope.device_id_seq(),
                               message.device.name,
                               scope.scaledX,
                               scope.scaledY,
                               message.device.type,
                               message.device.host_id);
    device.variables = message.device.variables;
    scope.update_links_in_vars_by_device(device.name, device.variables);
    scope.devices.push(device);
    scope.devices_by_name[message.device.name] = device;
    c_messages.push(new messages.DeviceCreate(scope.client_id,
                                              device.id,
                                              device.x,
                                              device.y,
                                              device.name,
                                              device.type,
                                              device.host_id));
    for (i=0; i < message.device.interfaces.length; i++) {
        intf = new models.Interface(message.device.interfaces[i].id, message.device.interfaces[i].name);
        device.interfaces.push(intf);
        device.interfaces_by_name[message.device.interfaces[i].name] = intf;
        intf.device = device;
        c_messages.push(new messages.InterfaceCreate(controller.scope.client_id,
                                                     device.id,
                                                     intf.id,
                                                     intf.name));
    }
    if (scope.links_in_vars_by_device[device.name] !== undefined) {
        for (i=0; i < scope.links_in_vars_by_device[device.name].length; i++) {
            link = scope.links_in_vars_by_device[device.name][i];
            if (device.interfaces_by_name[link.from_interface] === undefined) {
                intf = new models.Interface(device.interface_seq(), link.from_interface);
                device.interfaces.push(intf);
                device.interfaces_by_name[link.from_interface] = intf;
                intf.device = device;
                c_messages.push(new messages.InterfaceCreate(controller.scope.client_id,
                                                             device.id,
                                                             intf.id,
                                                             intf.name));
            }
            if (scope.devices_by_name[link.to_device] !== undefined) {
                remote_device = scope.devices_by_name[link.to_device];
                if (remote_device.interfaces_by_name[link.to_interface] === undefined) {
                    intf = new models.Interface(remote_device.interface_seq(), link.to_interface);
                    remote_device.interfaces.push(intf);
                    remote_device.interfaces_by_name[link.to_interface] = intf;
                    intf.device = remote_device;
                    c_messages.push(new messages.InterfaceCreate(controller.scope.client_id,
                                                                 remote_device.id,
                                                                 intf.id,
                                                                 intf.name));
                }
            }
            if (scope.devices_by_name[link.to_device] === undefined) {
                continue;
            }
            if (scope.devices_by_name[link.to_device].interfaces_by_name[link.to_interface] === undefined) {
                continue;
            }
            new_link = new models.Link(scope.link_id_seq(),
                                       device,
                                       scope.devices_by_name[link.to_device],
                                       device.interfaces_by_name[link.from_interface],
                                       scope.devices_by_name[link.to_device].interfaces_by_name[link.to_interface]);
            c_messages.push(new messages.LinkCreate(controller.scope.client_id,
                                                    new_link.id,
                                                    new_link.from_device.id,
                                                    new_link.to_device.id,
                                                    new_link.from_interface.id,
                                                    new_link.to_interface.id));
            device.interfaces_by_name[link.from_interface].link = new_link;
            scope.devices_by_name[link.to_device].interfaces_by_name[link.to_interface].link = new_link;
            scope.links.push(new_link);
            scope.updateInterfaceDots();
        }
    }
    scope.selected_devices.push(device);
    device.selected = true;
    console.log(c_messages);
    scope.send_control_message(new messages.MultipleMessage(controller.scope.client_id, c_messages));
    controller.changeState(Selected2);
};
_Ready.prototype.onPasteDevice.transitions = ['Selected2'];

_Ready.prototype.onMouseDown = function (controller, msg_type, $event) {

    var last_selected = controller.scope.select_items($event.shiftKey);

    if (last_selected.last_selected_device !== null) {
        controller.changeState(Selected1);
    } else if (last_selected.last_selected_link !== null) {
        controller.changeState(Selected1);
    } else if (last_selected.last_selected_interface !== null) {
        controller.changeState(Selected1);
    } else {
        controller.delegate_channel.send(msg_type, $event);
    }
};
_Ready.prototype.onMouseDown.transitions = ['Selected1'];

_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Selected2.prototype.onMouseDown = function (controller, msg_type, $event) {

	var last_selected = null;

    if (controller.scope.selected_devices.length === 1) {
        var current_selected_device = controller.scope.selected_devices[0];
        var last_selected_device = controller.scope.select_items($event.shiftKey).last_selected_device;
        if (current_selected_device === last_selected_device) {
            controller.changeState(Selected3);
            return;
        }
    }

    if (controller.scope.selected_links.length === 1) {
        var current_selected_link = controller.scope.selected_links[0];
        last_selected = controller.scope.select_items($event.shiftKey);
        if (current_selected_link === last_selected.last_selected_link) {
            controller.changeState(Selected3);
            return;
        }
    }

    if (controller.scope.selected_interfaces.length === 1) {
        var current_selected_interface = controller.scope.selected_interfaces[0];
        last_selected = controller.scope.select_items($event.shiftKey);
        if (current_selected_interface === last_selected.last_selected_interface) {
            controller.changeState(Selected3);
            return;
        }
    }
    controller.scope.first_channel.send('BindDocument', {});
    controller.changeState(Ready);
    controller.handle_message(msg_type, $event);
};
_Selected2.prototype.onMouseDown.transitions = ['Ready', 'Selected3'];

_Selected2.prototype.onKeyDown = function (controller, msg_type, $event) {

    if ($event.keyCode === 8) {
        //Delete
        controller.scope.deleteDevice();
    }

    controller.delegate_channel.send(msg_type, $event);
};
_Selected2.prototype.onKeyDown.transitions = ['Ready'];

_Selected1.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Selected1.prototype.onMouseMove.transitions = ['Move'];

_Selected1.prototype.onMouseUp = function (controller) {

    if(controller.scope.$parent.vm.rightPanelIsExpanded){
        controller.scope.onDetailsContextButton();
    }
    controller.changeState(Selected2);

};
_Selected1.prototype.onMouseUp.transitions = ['Selected2'];

_Selected1.prototype.onMouseDown = util.noop;

_Move.prototype.start = function (controller) {

    var devices = controller.scope.selected_devices;
    var i = 0;
    var j = 0;
    for (i = 0; i < devices.length; i++) {
        devices[i].moving = true;
        for (j = 0; j < controller.scope.devices.length; j++) {
            if ((Math.pow(devices[i].x - controller.scope.devices[j].x, 2) +
                 Math.pow(devices[i].y - controller.scope.devices[j].y, 2)) < 160000) {
                controller.scope.devices[j].moving = true;
            }
        }
    }
};

_Move.prototype.end = function (controller) {

    var devices = controller.scope.devices;
    var i = 0;
    for (i = 0; i < devices.length; i++) {
        devices[i].moving = false;
    }
};

_Move.prototype.onMouseMove = function (controller) {

    var devices = controller.scope.selected_devices;

    var diffX = controller.scope.scaledX - controller.scope.pressedScaledX;
    var diffY = controller.scope.scaledY - controller.scope.pressedScaledY;
    var i = 0;
    var j = 0;
    var previous_x, previous_y;
    for (i = 0; i < devices.length; i++) {
        previous_x = devices[i].x;
        previous_y = devices[i].y;
        devices[i].x = devices[i].x + diffX;
        devices[i].y = devices[i].y + diffY;
        for (j = 0; j < devices[i].interfaces.length; j++) {
             devices[i].interfaces[j].dot();
             if (devices[i].interfaces[j].link !== null) {
                 devices[i].interfaces[j].link.to_interface.dot();
                 devices[i].interfaces[j].link.from_interface.dot();
             }
        }
        controller.scope.send_control_message(new messages.DeviceMove(controller.scope.client_id,
                                                                      devices[i].id,
                                                                      devices[i].x,
                                                                      devices[i].y,
                                                                      previous_x,
                                                                      previous_y));
    }
    controller.scope.pressedScaledX = controller.scope.scaledX;
    controller.scope.pressedScaledY = controller.scope.scaledY;

};

_Move.prototype.onMouseUp = function (controller, msg_type, $event) {

    controller.changeState(Selected1);
    controller.handle_message(msg_type, $event);
};
_Move.prototype.onMouseUp.transitions = ['Selected1'];

_Move.prototype.onMouseDown = function (controller) {

    controller.changeState(Selected1);
};
_Move.prototype.onMouseDown.transitions = ['Selected1'];

_Selected3.prototype.onMouseUp = function (controller, msg_type, $event) {
    let context_menu = controller.scope.context_menus[0];
    context_menu.enabled = true;
    context_menu.x = $event.x;
    context_menu.y = $event.y;
    context_menu.buttons.forEach(function(button, index){
        button.x = $event.x;
        let menuPaddingTop = 5;
        button.y = $event.y + menuPaddingTop + (button.height * index);
    });

    controller.changeState(ContextMenu);
};
_Selected3.prototype.onMouseUp.transitions = ['ContextMenu'];

_Selected3.prototype.onMouseMove = function (controller) {
    controller.changeState(Move);
};
_Selected3.prototype.onMouseMove.transitions = ['Move'];

_Placing.prototype.onMouseDown = function (controller) {

    controller.changeState(Selected1);

};
_Placing.prototype.onMouseDown.transitions = ['Selected1'];

_Placing.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Placing.prototype.onMouseMove.transitions = ['Move'];


_ContextMenu.prototype.end = function (controller) {

    controller.scope.removeContextMenu();
};

_ContextMenu.prototype.onMouseDown = function (controller) {

    controller.changeState(Selected2);

};
_ContextMenu.prototype.onMouseDown.transitions = ['Selected2'];

_ContextMenu.prototype.onDetailsPanel = function (controller, msg_type, $event) {

    controller.changeState(Selected2);
    controller.handle_message(msg_type, $event);
};
_ContextMenu.prototype.onDetailsPanel.transitions = ['Selected2'];
