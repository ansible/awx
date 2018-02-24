/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var models = require('./models.js');
var messages = require('./messages.js');

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


function _Selected1 () {
    this.name = 'Selected1';
}
inherits(_Selected1, _State);
var Selected1 = new _Selected1();
exports.Selected1 = Selected1;

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

function _EditLabel () {
    this.name = 'EditLabel';
}
inherits(_EditLabel, _State);
var EditLabel = new _EditLabel();
exports.EditLabel = EditLabel;


function _Move () {
    this.name = 'Move';
}
inherits(_Move, _State);
var Move = new _Move();
exports.Move = Move;


function _ContextMenu () {
    this.name = 'ContextMenu';
}
inherits(_ContextMenu, _State);
var ContextMenu = new _ContextMenu();
exports.ContextMenu = ContextMenu;



_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Ready.prototype.onPasteSite = function (controller, msg_type, message) {

	var scope = controller.scope;
    var device = null;
    var intf = null;
    var process = null;
    var link = null;
    var stream = null;
    var i = 0;
    var j = 0;
    var top_left_x, top_left_y;
    var device_map = {};
    var inner_group = null;
    var c_messages = [];
    var membership_old_new = null;
    scope.hide_groups = false;

    scope.pressedX = scope.mouseX;
    scope.pressedY = scope.mouseY;
    scope.pressedScaledX = scope.scaledX;
    scope.pressedScaledY = scope.scaledY;
    top_left_x = scope.scaledX - message.group.x2/2;
    top_left_y = scope.scaledY - message.group.y2/2;

    var group = new models.Group(controller.scope.group_id_seq(),
                                 message.group.name,
                                 message.group.type,
                                 top_left_x,
                                 top_left_y,
                                 top_left_x + message.group.x2,
                                 top_left_y + message.group.y2,
                                 false);

    c_messages.push(new messages.GroupCreate(scope.client_id,
                                             group.id,
                                             group.x1,
                                             group.y1,
                                             group.x2,
                                             group.y2,
                                             group.name,
                                             group.type,
                                             0));

    scope.groups.push(group);

    for(i=0; i<message.group.devices.length;i++) {

        device = new models.Device(controller.scope.device_id_seq(),
                                   message.group.devices[i].name,
                                   top_left_x + message.group.devices[i].x,
                                   top_left_y + message.group.devices[i].y,
                                   message.group.devices[i].type);
        device_map[message.group.devices[i].id] = device;
        device.interface_map = {};
        scope.devices.push(device);
        group.devices.push(device);
        c_messages.push(new messages.DeviceCreate(scope.client_id,
                                                  device.id,
                                                  device.x,
                                                  device.y,
                                                  device.name,
                                                  device.type,
                                                  device.host_id));
        for (j=0; j < message.group.devices[i].interfaces.length; j++) {
            intf = new models.Interface(message.group.devices[i].interfaces[j].id, message.group.devices[i].interfaces[j].name);
            intf.device = device;
            device.interfaces.push(intf);
            device.interface_map[intf.id] = intf;
            c_messages.push(new messages.InterfaceCreate(controller.scope.client_id,
                                                         device.id,
                                                         intf.id,
                                                         intf.name));
        }
        for (j=0; j < message.group.devices[i].processes.length; j++) {
            process = new models.Process(message.group.devices[i].processes[j].id,
                                         message.group.devices[i].processes[j].name,
                                         message.group.devices[i].processes[j].type, 0, 0);
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
    }

    for(i=0; i<message.group.links.length;i++) {
        link = new models.Link(controller.scope.link_id_seq(),
                               device_map[message.group.links[i].from_device.id],
                               device_map[message.group.links[i].to_device.id],
                               device_map[message.group.links[i].from_device.id].interface_map[message.group.links[i].from_interface.id],
                               device_map[message.group.links[i].to_device.id].interface_map[message.group.links[i].to_interface.id]);
        link.name = message.group.links[i].name;
        device_map[message.group.links[i].from_device.id].interface_map[message.group.links[i].from_interface.id].link = link;
        device_map[message.group.links[i].to_device.id].interface_map[message.group.links[i].to_interface.id].link = link;
        device_map[message.group.links[i].from_device.id].interface_map[message.group.links[i].from_interface.id].dot();
        device_map[message.group.links[i].to_device.id].interface_map[message.group.links[i].to_interface.id].dot();
        scope.links.push(link);
        c_messages.push(new messages.LinkCreate(controller.scope.client_id,
                                                link.id,
                                                link.from_device.id,
                                                link.to_device.id,
                                                link.from_interface.id,
                                                link.to_interface.id));
    }

    for(i=0; i<message.group.streams.length;i++) {
        stream = new models.Stream(controller.scope.stream_id_seq(),
                                   device_map[message.group.streams[i].from_device.id],
                                   device_map[message.group.streams[i].to_device.id],
                                   message.group.streams[i].label);
        stream.name = message.group.streams[i].name;
        c_messages.push(new messages.StreamCreate(controller.scope.client_id,
                                                  stream.id,
                                                  stream.from_device.id,
                                                  stream.to_device.id,
                                                  stream.name));
        scope.streams.push(stream);
    }

    for(i=0; i<message.group.groups.length;i++) {
        inner_group = new models.Group(controller.scope.group_id_seq(),
                                       message.group.groups[i].name,
                                       message.group.groups[i].type,
                                       top_left_x + message.group.groups[i].x1,
                                       top_left_y + message.group.groups[i].y1,
                                       top_left_x + message.group.groups[i].x2,
                                       top_left_y + message.group.groups[i].y2,
                                       false);
        scope.groups.push(inner_group);
        group.groups.push(inner_group);
        c_messages.push(new messages.GroupCreate(scope.client_id,
                                                 inner_group.id,
                                                 inner_group.x1,
                                                 inner_group.y1,
                                                 inner_group.x2,
                                                 inner_group.y2,
                                                 inner_group.name,
                                                 inner_group.type,
                                                 0));
    }
    for(i=0; i< group.groups.length; i++) {
        membership_old_new = group.groups[i].update_membership(scope.devices, scope.groups);
        c_messages.push(new messages.GroupMembership(controller.scope.client_id,
                                                     group.groups[i].id,
                                                     membership_old_new[2]));
        controller.scope.create_group_association(groups[i], membership_old_new[6]);
        controller.scope.delete_group_association(groups[i], membership_old_new[7]);
    }

    membership_old_new = group.update_membership(scope.devices, scope.groups);
    c_messages.push(new messages.GroupMembership(controller.scope.client_id,
                                                 group.id,
                                                 membership_old_new[2]));
    controller.scope.create_group_association(group, membership_old_new[6]);
    controller.scope.delete_group_association(group, membership_old_new[7]);

    scope.send_control_message(new messages.MultipleMessage(controller.scope.client_id, c_messages));
};


_Selected1.prototype.onMouseUp = function (controller) {

    if(controller.scope.$parent.vm.rightPanelIsExpanded){
        controller.scope.onDetailsContextButton();
    }
    controller.changeState(Selected2);

};
_Selected1.prototype.onMouseUp.transitions = ['Selected2'];


_Selected1.prototype.onMouseMove = function (controller) {

    controller.changeState(Move);

};
_Selected1.prototype.onMouseMove.transitions = ['Move'];


_Selected2.prototype.onPasteSite = function (controller, msg_type, message) {

        controller.changeState(Ready);
        controller.handle_message(msg_type, message);
};

_Selected2.prototype.onCopySelected = function (controller) {

    var groups = controller.scope.selected_groups;
    var group_copy = null;
    var group = null;
    var inner_group = null;
    var devices = null;
    var device_copy = null;
    var process_copy = null;
    var interface_copy = null;
    var link_copy = null;
    var device_map = {};
    var streams = controller.scope.streams;
    var stream;
    var stream_copy;
    var i = 0;
    var j = 0;
    var k = 0;
    for(i=0; i < groups.length; i++) {
        group = groups[i];
        group_copy = new models.Group(0,
                                      group.name,
                                      group.type,
                                      0,
                                      0,
                                      group.right_extent() - group.left_extent(),
                                      group.bottom_extent() - group.top_extent(),
                                      false);
        group_copy.icon = true;

        devices = group.devices;

        for(j=0; j < devices.length; j++) {
            device_copy = new models.Device(devices[j].id,
                                            devices[j].name,
                                            devices[j].x - group.left_extent(),
                                            devices[j].y - group.top_extent(),
                                            devices[j].type);
            device_map[device_copy.id] = device_copy;
            device_copy.icon = true;
            device_copy.interface_map = {};
            for(k=0; k < devices[j].processes.length; k++) {
                process_copy = new models.Process(0, devices[j].processes[k].name, devices[j].processes[k].name, 0, 0);
                device_copy.processes.push(process_copy);
            }
            for(k=0; k < devices[j].interfaces.length; k++) {
                interface_copy = new models.Interface(devices[j].interfaces[k].id, devices[j].interfaces[k].name);
                device_copy.interfaces.push(interface_copy);
                device_copy.interface_map[interface_copy.id] = interface_copy;
            }
            group_copy.devices.push(device_copy);
        }

        group_copy.link_ids = [];

        for(j=0; j < devices.length; j++) {
            for(k=0; k < devices[j].interfaces.length; k++) {
                if (devices[j].interfaces[k].link !== null) {
                    if ((devices.indexOf(devices[j].interfaces[k].remote_interface().device) !== -1) &&
                        (group_copy.link_ids.indexOf(devices[j].interfaces[k].link.id) === -1)) {
                        link_copy = new models.Link(devices[j].interfaces[k].link.id,
                                                    device_map[devices[j].interfaces[k].link.from_device.id],
                                                    device_map[devices[j].interfaces[k].link.to_device.id],
                                                    device_map[devices[j].interfaces[k].link.from_device.id].interface_map[devices[j].interfaces[k].link.from_interface.id],
                                                    device_map[devices[j].interfaces[k].link.to_device.id].interface_map[devices[j].interfaces[k].link.to_interface.id]);
                        link_copy.name = devices[j].interfaces[k].link.name;

                        group_copy.links.push(link_copy);
                        group_copy.link_ids.push(link_copy.id);
                    }
                }
            }
        }

        group_copy.stream_ids = [];


        for (j=0; j<streams.length;j++) {

            stream = streams[j];

            if ((devices.indexOf(stream.to_device) !== -1) &&
                (devices.indexOf(stream.from_device) !== -1)) {
                stream_copy = new models.Stream(0, device_map[stream.from_device.id], device_map[stream.to_device.id], stream.label);
                group_copy.streams.push(stream_copy);
            }
        }


        for (j=0; j<group.groups.length;j++) {
            inner_group = new models.Group(0,
                                           group.groups[j].name,
                                           group.groups[j].type,
                                           group.groups[j].left_extent() - group.left_extent(),
                                           group.groups[j].top_extent() - group.top_extent(),
                                           group.groups[j].right_extent() - group.left_extent(),
                                           group.groups[j].bottom_extent() - group.top_extent(),
                                           false);
            group_copy.groups.push(inner_group);
        }

        controller.scope.send_control_message(new messages.CopySite(group_copy));

        controller.scope.site_toolbox.items.push(group_copy);
    }
};

_Selected2.prototype.onKeyDown = function (controller, msg_type, $event) {

    //controller.changeState(Ready);
    controller.delegate_channel.send(msg_type, $event);

};
_Selected2.prototype.onKeyDown.transitions = ['Ready'];

_Selected2.prototype.onMouseDown = function (controller, msg_type, $event) {

    controller.scope.pressedScaledX = controller.scope.scaledX;
    controller.scope.pressedScaledY = controller.scope.scaledY;

    var groups = controller.scope.selected_groups;
    var i = 0;
    var selected = false;
    controller.scope.selected_groups = [];

    for (i = 0; i < groups.length; i++) {
        if (groups[i].type !== "site") {
            continue;
        }
        if (groups[i].is_icon_selected(controller.scope.scaledX, controller.scope.scaledY)) {
            groups[i].selected = true;
            selected = true;
            controller.scope.selected_groups.push(groups[i]);
        }
    }

    if (selected) {
        controller.changeState(Selected3);
    } else {
        for (i = 0; i < groups.length; i++) {
            groups[i].selected = false;
        }
        controller.changeState(Ready);
        controller.handle_message(msg_type, $event);
    }
};
_Selected2.prototype.onMouseDown.transitions = ['Selected3', 'Ready'];



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
    controller.scope.selected_groups[0].edit_label = true;
};

_EditLabel.prototype.end = function (controller) {
    controller.scope.selected_groups[0].edit_label = false;
};


_EditLabel.prototype.onMouseDown = function (controller, msg_type, $event) {

    controller.changeState(Ready);
    controller.handle_message(msg_type, $event);
};
_EditLabel.prototype.onMouseDown.transitions = ['Ready'];


_EditLabel.prototype.onKeyDown = function (controller, msg_type, $event) {
    //Key codes found here:
    //https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
	var item = controller.scope.selected_groups[0];
    var previous_name = item.name;
	if ($event.keyCode === 8 || $event.keyCode === 46) { //Delete
		item.name = item.name.slice(0, -1);
	} else if ($event.keyCode >= 48 && $event.keyCode <=90) { //Alphanumeric
        item.name += $event.key;
	} else if ($event.keyCode >= 186 && $event.keyCode <=222) { //Punctuation
        item.name += $event.key;
	} else if ($event.keyCode === 13) { //Enter
        controller.changeState(Selected2);
	} else if ($event.keyCode === 32) { //Space
        item.name += " ";
    } else {
        console.log($event.keyCode);
    }
    controller.scope.send_control_message(new messages.GroupLabelEdit(controller.scope.client_id,
                                                                      item.id,
                                                                      item.name,
                                                                      previous_name));
};
_EditLabel.prototype.onKeyDown.transitions = ['Selected2'];


_Ready.prototype.onMouseDown = function (controller, msg_type, $event) {

    controller.scope.pressedScaledX = controller.scope.scaledX;
    controller.scope.pressedScaledY = controller.scope.scaledY;

    var groups = controller.scope.groups;
    var i = 0;
    var selected = false;
    controller.scope.clear_selections();

    for (i = 0; i < groups.length; i++) {
        if (groups[i].type !== "site") {
            continue;
        }
        if (groups[i].is_icon_selected(controller.scope.scaledX, controller.scope.scaledY)) {
            groups[i].selected = true;
            selected = true;
            controller.scope.selected_groups.push(groups[i]);
        }
    }

    if (selected) {
        controller.changeState(Selected1);
    } else {
        controller.delegate_channel.send(msg_type, $event);
    }
};
_Ready.prototype.onMouseDown.transitions = ['Selected1'];

_Move.prototype.start = function (controller) {

    var groups = controller.scope.selected_groups;

    var i = 0;
    for (i = 0; i < groups.length; i++) {
        groups[i].moving = true;
    }
};

_Move.prototype.end = function (controller) {

    var groups = controller.scope.selected_groups;

    var i = 0;
    var j = 0;
    for (i = 0; i < groups.length; i++) {
        for(j = 0; j < groups[i].devices.length; j++) {
            groups[i].devices[j].selected = false;
        }
    }

    for (i = 0; i < groups.length; i++) {
        groups[i].moving = false;
    }
};

_Move.prototype.onMouseUp = function (controller) {

    controller.changeState(Selected2);

};
_Move.prototype.onMouseUp.transitions = ['Selected2'];


_Move.prototype.onMouseMove = function (controller) {

    var groups = controller.scope.selected_groups;
    var devices = null;

    var diffX = controller.scope.scaledX - controller.scope.pressedScaledX;
    var diffY = controller.scope.scaledY - controller.scope.pressedScaledY;
    var i = 0;
    var j = 0;
    var k = 0;
    var previous_x1, previous_y1, previous_x2, previous_y2, previous_x, previous_y;
    var c_messages = [];
    for (i = 0; i < groups.length; i++) {
        c_messages = [];
        previous_x1 = groups[i].x1;
        previous_y1 = groups[i].y1;
        previous_x2 = groups[i].x2;
        previous_y2 = groups[i].y2;
        groups[i].x1 = groups[i].x1 + diffX;
        groups[i].y1 = groups[i].y1 + diffY;
        groups[i].x2 = groups[i].x2 + diffX;
        groups[i].y2 = groups[i].y2 + diffY;

        c_messages.push(new messages.GroupMove(controller.scope.client_id,
                                               groups[i].id,
                                               groups[i].x1,
                                               groups[i].y1,
                                               groups[i].x2,
                                               groups[i].y2,
                                               previous_x1,
                                               previous_y1,
                                               previous_x2,
                                               previous_y2));


        devices = groups[i].devices;
        for (j = 0; j < devices.length; j++) {
            previous_x = devices[j].x;
            previous_y = devices[j].y;
            devices[j].x = devices[j].x + diffX;
            devices[j].y = devices[j].y + diffY;
            for (k = 0; k < devices[j].interfaces.length; k++) {
                 devices[j].interfaces[k].dot();
                 if (devices[j].interfaces[k].link !== null) {
                     devices[j].interfaces[k].link.to_interface.dot();
                     devices[j].interfaces[k].link.from_interface.dot();
                 }
            }
            c_messages.push(new messages.DeviceMove(controller.scope.client_id,
                                                    devices[j].id,
                                                    devices[j].x,
                                                    devices[j].y,
                                                    previous_x,
                                                    previous_y));
        }
        for (j = 0; j < groups[i].groups.length; j++) {
            previous_x1 = groups[i].groups[j].x1;
            previous_y1 = groups[i].groups[j].y1;
            previous_x2 = groups[i].groups[j].x2;
            previous_y2 = groups[i].groups[j].y2;
            groups[i].groups[j].x1 = groups[i].groups[j].x1 + diffX;
            groups[i].groups[j].y1 = groups[i].groups[j].y1 + diffY;
            groups[i].groups[j].x2 = groups[i].groups[j].x2 + diffX;
            groups[i].groups[j].y2 = groups[i].groups[j].y2 + diffY;

            c_messages.push(new messages.GroupMove(controller.scope.client_id,
                                                   groups[i].groups[j].id,
                                                   groups[i].groups[j].x1,
                                                   groups[i].groups[j].y1,
                                                   groups[i].groups[j].x2,
                                                   groups[i].groups[j].y2,
                                                   previous_x1,
                                                   previous_y1,
                                                   previous_x2,
                                                   previous_y2));
        }

        controller.scope.send_control_message(new messages.MultipleMessage(controller.scope.client_id, c_messages));
    }
    controller.scope.pressedScaledX = controller.scope.scaledX;
    controller.scope.pressedScaledY = controller.scope.scaledY;

};

_Move.prototype.onTouchMove = _Move.prototype.onMouseMove;

_ContextMenu.prototype.end = function (controller) {

    controller.scope.removeContextMenu();
};

_ContextMenu.prototype.onLabelEdit = function (controller) {

    controller.changeState(EditLabel);

};
_ContextMenu.prototype.onLabelEdit.transitions = ['EditLabel'];

_ContextMenu.prototype.onMouseDown = function (controller) {

    controller.changeState(Ready);

};
_ContextMenu.prototype.onMouseDown.transitions = ['Ready'];
