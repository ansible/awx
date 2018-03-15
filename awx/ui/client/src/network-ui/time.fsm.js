/* Copyright (c) 2017 Red Hat, Inc. */
var inherits = require('inherits');
var fsm = require('./fsm.js');
var util = require('./util.js');

function _State () {
}
inherits(_State, fsm._State);

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
        if (message.graph_width !== undefined) {
            controller.scope.graph.width = message.graph_width;
        }
        if (message.graph_height !== undefined) {
            controller.scope.graph.height = message.graph_height;
        }
        controller.scope.update_toolbox_heights();
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

_Present.prototype.onRecordButton = function(controller) {
    controller.scope.onRecordButton();
};

_Present.prototype.onExportButton = function(controller) {
    controller.scope.onExportButton();
};

_Present.prototype.onExportYamlButton = function(controller) {
    controller.scope.onExportYamlButton();
};

_Present.prototype.onDownloadTraceButton = function(controller) {
    controller.scope.onDownloadTraceButton();
};

_Present.prototype.onDownloadRecordingButton = function(controller) {
    controller.scope.onDownloadRecordingButton();
};

_Present.prototype.onNoop = function(controller, msg_type, message) {

};

_Present.prototype.onTestCompleted = function(controller, msg_type, message) {

    controller.scope.test_channel.send(msg_type, message);
}


_Present.prototype.onError = function(controller, msg_type, message) {
    throw new Error("ServerError: " + message);
};
