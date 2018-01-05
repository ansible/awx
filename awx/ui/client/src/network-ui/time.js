/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var messages = require('./messages.js');
var util = require('./util.js');
var models = require('./models.js');

function _State () {
}
inherits(_State, fsm._State);

function _Past () {
    this.name = 'Past';
}
inherits(_Past, _State);
var Past = new _Past();
exports.Past = Past;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Present () {
    this.name = 'Present';
}
inherits(_Present, _State);
var Present = new _Present();
exports.Present = Present;

_Past.prototype.start = function (controller) {

    controller.scope.time_pointer = controller.scope.history.length - 1;
};


_Past.prototype.onMessage = function(controller, msg_type, message) {

    var type_data = JSON.parse(message.data);
    var type = type_data[0];
    var data = type_data[1];

    if (['DeviceCreate',
         'DeviceDestroy',
         'DeviceMove',
         'DeviceLabelEdit',
         'GroupLabelEdit',
         'GroupCreate',
         'LinkLabelEdit',
         'InterfaceLabelEdit',
         'InterfaceCreate',
         'LinkCreate',
         'LinkDestroy'].indexOf(type) !== -1) {
        controller.changeState(Present);
        controller.scope.history.splice(controller.scope.time_pointer);
        if (data.sender !== controller.scope.client_id) {
            controller.handle_message(msg_type, message);
        } else {
            controller.scope.history.push(message.data);
        }
    } else {
        controller.handle_message(type, data);
    }
};

_Past.prototype.onMultipleMessage = function(controller, msg_type, message) {
        var i = 0;
        if (message.sender !== controller.scope.client_id) {
            for (i=0; i< message.messages.length; i++) {
                controller.handle_message(message.messages[i].msg_type, message.messages[i]);
            }
        }
};

_Past.prototype.onDeviceSelected = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceSelected(message);
        }
};
_Past.prototype.onDeviceUnSelected = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceUnSelected(message);
        }
};

_Past.prototype.onUndo = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.time_pointer = Math.max(0, controller.scope.time_pointer - 1);
            controller.scope.undo(message.original_message);
        }
};
_Past.prototype.onRedo = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.time_pointer = Math.min(controller.scope.history.length, controller.scope.time_pointer + 1);
            controller.scope.redo(message.original_message);
            if (controller.scope.time_pointer === controller.scope.history.length) {
                controller.changeState(Present);
            }
        }
};
_Past.prototype.onRedo.transitions = ['Present'];

_Past.prototype.onCoverageRequest = function(controller) {
        controller.scope.send_coverage();
};
_Past.prototype.onStopRecording = function(controller) {
        controller.scope.recording = false;
};
_Past.prototype.onStartReplay = function(controller) {
        controller.scope.replay = true;
};
_Past.prototype.onStopReplay = function(controller) {
        controller.scope.replay = false;
};
_Past.prototype.onViewPort = function(controller, msg_type, message) {
        if (message.sender === controller.scope.client_id) {
            return;
        }
        controller.scope.current_scale = message.scale;
        controller.scope.panX = message.panX;
        controller.scope.panY = message.panY;
        controller.scope.updateScaledXY();
        controller.scope.updatePanAndScale();
};
_Past.prototype.onMouseEvent = function(controller, msg_type, message) {
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        if (message.type === "mousemove") {
            controller.scope.onMouseMove(message);
        }
        if (message.type === "mouseup") {
            controller.scope.onMouseUp(message);
        }
        if (message.type === "mousedown") {
            controller.scope.onMouseDown(message);
        }
        if (message.type === "mouseover") {
            controller.scope.onMouseOver(message);
        }
        if (message.type === "mouseout") {
            controller.scope.onMouseOver(message);
        }
};
_Past.prototype.onMouseWheelEvent = function(controller, msg_type, message) {
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        message.stopPropagation = util.noop;
        controller.scope.onMouseWheel(message, message.delta, message.deltaX, message.deltaY);
};
_Past.prototype.onKeyEvent = function(controller, msg_type, message) {
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        if (message.type === "keydown") {
            controller.scope.onKeyDown(message);
        }
};

_Past.prototype.onMouseWheel = function (controller, msg_type, message) {

    var $event = message[0];
    var delta = message[1];

    if ($event.originalEvent.metaKey) {
        if (delta < 0) {
            this.undo(controller);
        } else if (delta > 0) {
            this.redo(controller);
        }
    } else {
        controller.delegate_channel.send(msg_type, message);
    }

};
_Past.prototype.onMouseWheel.transitions = ['Present'];

_Past.prototype.onKeyDown = function(controller, msg_type, $event) {


    if ($event.key === 'z' && $event.metaKey && ! $event.shiftKey) {
        this.undo(controller);
        return;
    } else if ($event.key === 'z' && $event.ctrlKey && ! $event.shiftKey) {
        this.undo(controller);
        return;
    } else if ($event.key === 'Z' && $event.metaKey && $event.shiftKey) {
        this.redo(controller);
        return;
    } else if ($event.key === 'Z' && $event.ctrlKey && $event.shiftKey) {
        this.redo(controller);
        return;
    } else {
        controller.delegate_channel.send(msg_type, $event);
    }
};
_Past.prototype.onKeyDown.transitions = ['Present'];


_Past.prototype.undo = function(controller) {
    //controller.changeState(Past);
    controller.scope.time_pointer = Math.max(0, controller.scope.time_pointer - 1);
    if (controller.scope.time_pointer >= 0) {
        var change = controller.scope.history[controller.scope.time_pointer];
        var type_data = JSON.parse(change);
        controller.scope.send_control_message(new messages.Undo(controller.scope.client_id,
                                                                type_data));


        controller.scope.undo(type_data);
    }
};

_Past.prototype.redo = function(controller) {


    if (controller.scope.time_pointer < controller.scope.history.length) {
        var change = controller.scope.history[controller.scope.time_pointer];
        var type_data = JSON.parse(change);
        controller.scope.send_control_message(new messages.Redo(controller.scope.client_id,
                                                                type_data));
        controller.scope.redo(type_data);
        controller.scope.time_pointer = Math.min(controller.scope.history.length, controller.scope.time_pointer + 1);
        if (controller.scope.time_pointer === controller.scope.history.length) {
            controller.changeState(Present);
        }
    } else {
        controller.changeState(Present);
    }
};

_Start.prototype.start = function (controller) {

    controller.changeState(Present);

};
_Start.prototype.start.transitions = ['Present'];

_Present.prototype.onMessage = function(controller, msg_type, message) {

    var type_data = JSON.parse(message.data);
    var type = type_data[0];
    var data = type_data[1];


    if (['DeviceCreate',
         'DeviceDestroy',
         'DeviceMove',
         'DeviceLabelEdit',
         'GroupLabelEdit',
         'GroupCreate',
         'InterfaceCreate',
         'InterfaceLabelEdit',
         'LinkCreate',
         'LinkDestroy',
         'LinkLabelEdit',
         'Snapshot'].indexOf(type) !== -1) {

        controller.scope.history.push(message.data);
    }
    controller.handle_message(type, data);
};

_Present.prototype.onMultipleMessage = function(controller, msg_type, message) {

    var i = 0;
    if (message.sender !== controller.scope.client_id) {
        for (i = 0; i< message.messages.length; i++) {
            controller.handle_message(message.messages[i].msg_type, message.messages[i]);
        }
    }
};

_Present.prototype.onDeviceStatus = function(controller, msg_type, message) {
    controller.scope.onDeviceStatus(message);
};

_Present.prototype.onFacts = function(controller, msg_type, message) {
        controller.scope.onFacts(message);
};

_Present.prototype.onDeviceCreate = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceCreate(message);
        }
};
_Present.prototype.onGroupCreate = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onGroupCreate(message);
        }
};
_Present.prototype.onInterfaceCreate = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onInterfaceCreate(message);
        }
};
_Present.prototype.onLinkCreate = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onLinkCreate(message);
        }
};
_Present.prototype.onDeviceMove = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceMove(message);
        }
};
_Present.prototype.onDeviceDestroy = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceDestroy(message);
        }
};
_Present.prototype.onLinkDestroy = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onLinkDestroy(message);
        }
};
_Present.prototype.onDeviceLabelEdit = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceLabelEdit(message);
        }
};
_Present.prototype.onGroupLabelEdit = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onGroupLabelEdit(message);
        }
};
_Present.prototype.onLinkLabelEdit = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onLinkLabelEdit(message);
        }
};
_Present.prototype.onInterfaceLabelEdit = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onInterfaceLabelEdit(message);
        }
};
_Present.prototype.onDeviceSelected = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceSelected(message);
        }
};
_Present.prototype.onDeviceUnSelected = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onDeviceUnSelected(message);
        }
};
_Present.prototype.onUndo = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.time_pointer = Math.max(0, controller.scope.time_pointer - 1);
            controller.scope.undo(message.original_message);
            controller.changeState(Past);
        }
};
_Present.prototype.onUndo.transitions = ['Past'];
_Present.prototype.onSnapshot = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onSnapshot(message);
        }
};
_Present.prototype.onToolboxItem = function(controller, msg_type, message) {
        if (message.sender !== controller.scope.client_id) {
            controller.scope.onToolboxItem(message);
        }
};
_Present.prototype.onid = function(controller, msg_type, message) {
        controller.scope.onClientId(message);
};
_Present.prototype.onTopology = function(controller, msg_type, message) {
        controller.scope.onTopology(message);
};
_Present.prototype.onHistory = function(controller, msg_type, message) {
        controller.scope.onHistory(message);
};

_Present.prototype.onCoverageRequest = function(controller) {
        controller.scope.send_coverage();
};
_Present.prototype.onStopRecording = function(controller) {
        controller.scope.recording = false;
};
_Present.prototype.onStartReplay = function(controller) {
        controller.scope.replay = true;
};
_Present.prototype.onStopReplay = function(controller) {
        controller.scope.replay = false;
};
_Present.prototype.onViewPort = function(controller, msg_type, message) {
        if (message.sender === controller.scope.client_id) {
            return;
        }
        controller.scope.current_scale = message.scale;
        controller.scope.panX = message.panX;
        controller.scope.panY = message.panY;
        controller.scope.updateScaledXY();
        controller.scope.updatePanAndScale();
};
_Present.prototype.onMouseEvent = function(controller, msg_type, message) {
        if (!controller.scope.replay) {
            return;
        }
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        if (message.type === "mousemove") {
            controller.scope.onMouseMove(message);
        }
        if (message.type === "mouseup") {
            controller.scope.onMouseUp(message);
        }
        if (message.type === "mousedown") {
            controller.scope.onMouseDown(message);
        }
        if (message.type === "mouseover") {
            controller.scope.onMouseOver(message);
        }
};
_Present.prototype.onMouseWheelEvent = function(controller, msg_type, message) {
        if (!controller.scope.replay) {
            return;
        }
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        message.stopPropagation = util.noop;
        controller.scope.onMouseWheel(message, message.delta, message.deltaX, message.deltaY);
};
 _Present.prototype.onKeyEvent = function(controller, msg_type, message) {
        if (!controller.scope.replay) {
            return;
        }
        if (message.sender === controller.scope.client_id) {
            return;
        }
        message.preventDefault = util.noop;
        if (message.type === "keydown") {
            controller.scope.onKeyDown(message);
        }
};

_Present.prototype.onMouseWheel = function (controller, msg_type, message) {

    var $event = message[0];
    var delta = message[1];

    if ($event.originalEvent.metaKey) {
        if (delta < 0) {
            this.undo(controller);
        }
    } else {
        controller.delegate_channel.send(msg_type, message);
    }

};
_Present.prototype.onMouseWheel.transitions = ['Past'];

_Present.prototype.onKeyDown = function(controller, msg_type, $event) {


    if ($event.key === 'z' && $event.metaKey && ! $event.shiftKey) {
        this.undo(controller);
        return;
    } else if ($event.key === 'z' && $event.ctrlKey && ! $event.shiftKey) {
        this.undo(controller);
        return;
    } else {
        controller.delegate_channel.send(msg_type, $event);
    }
};
_Present.prototype.onKeyDown.transitions = ['Past'];


_Present.prototype.undo = function(controller) {
    controller.scope.time_pointer = controller.scope.history.length - 1;
    if (controller.scope.time_pointer >= 0) {
        var change = controller.scope.history[controller.scope.time_pointer];
        var type_data = JSON.parse(change);
        controller.scope.send_control_message(new messages.Undo(controller.scope.client_id,
                                                                type_data));

        controller.scope.undo(type_data);
        controller.changeState(Past);
    }
};


_Present.prototype.onTestCase = function(controller, msg_type, message) {
    if ('runnable' in message[1]) {
        if (!message[1].runnable) {
            return;
        }
    }
    controller.scope.tests.push(new models.Test(message[0],
                                                message[1].event_trace,
                                                [],
                                                message[1].snapshots[0],
                                                message[1].snapshots[1]));
};

_Present.prototype.onError = function(controller, msg_type, message) {
    throw new Error("ServerError: " + message);
};
