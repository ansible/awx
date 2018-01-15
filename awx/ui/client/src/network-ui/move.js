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



function _EditLabel () {
    this.name = 'EditLabel';
}
inherits(_EditLabel, _State);
var EditLabel = new _EditLabel();
exports.EditLabel = EditLabel;


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

_Ready.prototype.onNewDevice = function (controller, msg_type, message) {

	var scope = controller.scope;
    var device = null;
    var id = null;

    scope.pressedX = scope.mouseX;
    scope.pressedY = scope.mouseY;
    scope.pressedScaledX = scope.scaledX;
    scope.pressedScaledY = scope.scaledY;

    scope.clear_selections();

	if (message.type === "router") {
        id = controller.scope.device_id_seq();
		device = new models.Device(id,
                                   "Router" + id,
                                   scope.scaledX,
                                   scope.scaledY,
                                   "router");
	}
    else if (message.type === "switch") {
        id = controller.scope.device_id_seq();
		device = new models.Device(id,
                                   "Switch" + id,
                                   scope.scaledX,
                                   scope.scaledY,
                                   "switch");
	}
    else if (message.type === "host") {
        id = controller.scope.device_id_seq();
		device = new models.Device(id,
                                   "Host" + id,
                                   scope.scaledX,
                                   scope.scaledY,
                                   "host");
	}

    if (device !== null) {
        scope.devices.push(device);
        scope.send_control_message(new messages.DeviceCreate(scope.client_id,
                                                             device.id,
                                                             device.x,
                                                             device.y,
                                                             device.name,
                                                             device.type,
                                                             device.host_id));
        scope.selected_devices.push(device);
        device.selected = true;
        controller.changeState(Placing);
    }
};
_Ready.prototype.onNewDevice.transitions = ['Placing'];

_Ready.prototype.onPasteDevice = function (controller, msg_type, message) {

	var scope = controller.scope;
    var device = null;
    var intf = null;
    var process = null;
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
    scope.devices.push(device);
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
        c_messages.push(new messages.InterfaceCreate(controller.scope.client_id,
                                                     device.id,
                                                     intf.id,
                                                     intf.name));
    }
    for (i=0; i < message.device.processes.length; i++) {
        process = new models.Process(message.device.processes[i].id,
                                     message.device.processes[i].name,
                                     message.device.processes[i].type, 0, 0);
        process.device = device;
        c_messages.push(new messages.ProcessCreate(controller.scope.client_id,
                                                   process.id,
                                                   process.name,
                                                   process.type,
                                                   process.device.id,
                                                   process.x,
                                                   process.y));
        device.processes.push(process);
    }
    scope.selected_devices.push(device);
    device.selected = true;
    scope.send_control_message(new messages.MultipleMessage(controller.scope.client_id, c_messages));
    controller.changeState(Selected2);
};
_Ready.prototype.onPasteDevice.transitions = ['Selected2'];

_Ready.prototype.onMouseDown = function (controller, msg_type, $event) {

    var last_selected = controller.scope.select_items($event.shiftKey);

    if (last_selected.last_selected_device !== null) {
        controller.changeState(Selected1);
        controller.scope.onDetailsContextButton();
    } else if (last_selected.last_selected_link !== null) {
        controller.changeState(Selected1);
        controller.scope.onDetailsContextButton();
    } else if (last_selected.last_selected_interface !== null) {
        controller.changeState(Selected1);
        controller.scope.onDetailsContextButton();
    } else {
        controller.delegate_channel.send(msg_type, $event);
    }
};
_Ready.prototype.onMouseDown.transitions = ['Selected1'];

_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Selected2.prototype.onNewDevice = function (controller, msg_type, message) {

    controller.changeState(Ready);
    controller.handle_message(msg_type, message);
};
_Selected2.prototype.onNewDevice.transitions = ['Ready'];

_Selected2.prototype.onCopySelected = function (controller) {

    var devices = controller.scope.selected_devices;
    var device_copy = null;
    var process_copy = null;
    var interface_copy = null;
    var i = 0;
    var j = 0;
    for(i=0; i < devices.length; i++) {
        device_copy = new models.Device(0, devices[i].name, 0, 0, devices[i].type);
        device_copy.icon = true;
        for(j=0; j < devices[i].processes.length; j++) {
            process_copy = new models.Process(0, devices[i].processes[j].name, devices[i].processes[j].name, 0, 0);
            device_copy.processes.push(process_copy);
        }
        for(j=0; j < devices[i].interfaces.length; j++) {
            interface_copy = new models.Interface(devices[i].interfaces[j].id, devices[i].interfaces[j].name);
            device_copy.interfaces.push(interface_copy);
        }
        controller.scope.inventory_toolbox.items.push(device_copy);
    }
};

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

    controller.changeState(Ready);
    controller.handle_message(msg_type, $event);
};
_Selected2.prototype.onMouseDown.transitions = ['Ready', 'Selected3'];

_Selected2.prototype.onKeyDown = function (controller, msg_type, $event) {

    if ($event.keyCode === 8) {
        //Delete
        controller.changeState(Ready);

        var i = 0;
        var j = 0;
        var index = -1;
        var devices = controller.scope.selected_devices;
        var links = controller.scope.selected_links;
        var all_links = controller.scope.links.slice();
        controller.scope.selected_devices = [];
        controller.scope.selected_links = [];
        for (i = 0; i < links.length; i++) {
            index = controller.scope.links.indexOf(links[i]);
            if (index !== -1) {
                links[i].selected = false;
                links[i].remote_selected = false;
                controller.scope.links.splice(index, 1);
                controller.scope.send_control_message(new messages.LinkDestroy(controller.scope.client_id,
                                                                               links[i].id,
                                                                               links[i].from_device.id,
                                                                               links[i].to_device.id,
                                                                               links[i].from_interface.id,
                                                                               links[i].to_interface.id,
                                                                               links[i].name));
            }
        }
        for (i = 0; i < devices.length; i++) {
            index = controller.scope.devices.indexOf(devices[i]);
            if (index !== -1) {
                controller.scope.devices.splice(index, 1);
                controller.scope.send_control_message(new messages.DeviceDestroy(controller.scope.client_id,
                                                                                 devices[i].id,
                                                                                 devices[i].x,
                                                                                 devices[i].y,
                                                                                 devices[i].name,
                                                                                 devices[i].type,
                                                                                 devices[i].host_id));
            }
            for (j = 0; j < all_links.length; j++) {
                if (all_links[j].to_device === devices[i] ||
                    all_links[j].from_device === devices[i]) {
                    index = controller.scope.links.indexOf(all_links[j]);
                    if (index !== -1) {
                        controller.scope.links.splice(index, 1);
                    }
                }
            }
        }
    }

    controller.delegate_channel.send(msg_type, $event);
};
_Selected2.prototype.onKeyDown.transitions = ['Ready'];

_Selected1.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Selected1.prototype.onMouseMove.transitions = ['Move'];

_Selected1.prototype.onMouseUp = function (controller) {

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
    var groups = controller.scope.groups;

    var diffX = controller.scope.scaledX - controller.scope.pressedScaledX;
    var diffY = controller.scope.scaledY - controller.scope.pressedScaledY;
    var i = 0;
    var j = 0;
    var previous_x, previous_y;
    var membership_old_new;
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


    //TODO: Improve the performance of this code from O(n^2) to O(n) or better
    for (i = 0; i < groups.length; i++) {
        membership_old_new = groups[i].update_membership(controller.scope.devices, controller.scope.groups);
        controller.scope.send_control_message(new messages.GroupMembership(controller.scope.client_id,
                                                                           groups[i].id,
                                                                           membership_old_new[2]));
    }
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

_EditLabel.prototype.start = function (controller) {
    controller.scope.selected_items[0].edit_label = true;
};

_EditLabel.prototype.end = function (controller) {
    controller.scope.selected_items[0].edit_label = false;
};

_EditLabel.prototype.onMouseDown = function (controller, msg_type, $event) {

    controller.changeState(Ready);
    controller.handle_message(msg_type, $event);

};
_EditLabel.prototype.onMouseDown.transitions = ['Ready'];


_EditLabel.prototype.onKeyDown = function (controller, msg_type, $event) {
    //Key codes found here:
    //https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
	var item = controller.scope.selected_items[0];
    var previous_name = item.name;
	if ($event.keyCode === 8 || $event.keyCode === 46) { //Delete
		item.name = item.name.slice(0, -1);
	} else if ($event.keyCode >= 48 && $event.keyCode <=90) { //Alphanumeric
        item.name += $event.key;
	} else if ($event.keyCode >= 186 && $event.keyCode <=222) { //Punctuation
        item.name += $event.key;
	} else if ($event.keyCode === 13) { //Enter
        controller.changeState(Selected2);
    }
    if (item.constructor.name === "Device") {
        controller.scope.send_control_message(new messages.DeviceLabelEdit(controller.scope.client_id,
                                                                           item.id,
                                                                           item.name,
                                                                           previous_name));
    }
    if (item.constructor.name === "Interface") {
        controller.scope.send_control_message(new messages.InterfaceLabelEdit(controller.scope.client_id,
                                                                           item.id,
                                                                           item.device.id,
                                                                           item.name,
                                                                           previous_name));
    }
    if (item.constructor.name === "Link") {
        controller.scope.send_control_message(new messages.LinkLabelEdit(controller.scope.client_id,
                                                                           item.id,
                                                                           item.name,
                                                                           previous_name));
    }
};
_EditLabel.prototype.onKeyDown.transitions = ['Selected2'];


_Placing.prototype.onMouseDown = function (controller) {

    controller.changeState(Selected1);

};
_Placing.prototype.onMouseDown.transitions = ['Selected1'];

_Placing.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Placing.prototype.onMouseMove.transitions = ['Move'];





_ContextMenu.prototype.onLabelEdit = function (controller) {

    controller.changeState(EditLabel);

};
_ContextMenu.prototype.onLabelEdit.transitions = ['EditLabel'];

_ContextMenu.prototype.onMouseDown = function (controller) {

    var item = controller.scope.context_menus[0];
    item.enabled = false;
    controller.changeState(Ready);

};
_ContextMenu.prototype.onMouseDown.transitions = ['Ready'];
