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






_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Ready.prototype.onPasteSite = function (controller, msg_type, message) {

	var scope = controller.scope;
    scope.hide_groups = false;

    scope.pressedX = scope.mouseX;
    scope.pressedY = scope.mouseY;
    scope.pressedScaledX = scope.scaledX;
    scope.pressedScaledY = scope.scaledY;

    var group = new models.Group(controller.scope.group_id_seq(),
                                 message.group.name,
                                 message.group.type,
                                 scope.scaledX,
                                 scope.scaledY,
                                 scope.scaledX + message.group.x2,
                                 scope.scaledY + message.group.y2,
                                 false);

    scope.send_control_message(new messages.GroupCreate(scope.client_id,
                                                        group.id,
                                                        group.x1,
                                                        group.y1,
                                                        group.x2,
                                                        group.y2,
                                                        group.name,
                                                        group.type));

    scope.groups.push(group);
};


_Selected1.prototype.onMouseUp = function (controller) {

    controller.changeState(Selected2);

};
_Selected1.prototype.onMouseUp.transitions = ['Selected2'];



_Selected2.prototype.onCopySelected = function (controller) {

    var groups = controller.scope.selected_groups;
    var group_copy = null;
    var group = null;
    var i = 0;
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
        controller.scope.site_toolbox.items.push(group_copy);
    }
};

_Selected2.prototype.onKeyDown = function (controller, msg_type, $event) {

    //controller.changeState(Ready);
    controller.next_controller.handle_message(msg_type, $event);

};
_Selected2.prototype.onKeyDown.transitions = ['Ready'];

_Selected2.prototype.onMouseDown = function (controller, msg_type, $event) {

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



_Selected3.prototype.onMouseUp = function (controller) {

    controller.changeState(EditLabel);

};
_Selected3.prototype.onMouseUp.transitions = ['EditLabel'];



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
        controller.next_controller.handle_message(msg_type, $event);
    }
};
_Ready.prototype.onMouseDown.transitions = ['Selected1'];
