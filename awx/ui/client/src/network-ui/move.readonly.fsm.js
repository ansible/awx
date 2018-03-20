/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
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

function _Selected1 () {
    this.name = 'Selected1';
}
inherits(_Selected1, _State);
var Selected1 = new _Selected1();
exports.Selected1 = Selected1;

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


_Selected1.prototype.onMouseUp = function (controller) {

    if(controller.scope.$parent.vm.rightPanelIsExpanded){
        controller.scope.onDetailsContextButton();
    }
    controller.changeState(Selected2);

};
_Selected1.prototype.onMouseUp.transitions = ['Selected2'];

_Selected1.prototype.onMouseDown = util.noop;

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
    controller.changeState(Selected2);
};
_Selected3.prototype.onMouseMove.transitions = ['Selected2'];

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
