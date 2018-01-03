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






_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};
_Start.prototype.start.transitions = ['Ready'];


_Ready.prototype.onPasteProcess = function (controller, msg_type, message) {

    console.log([msg_type, message]);

    var i=0;
    var devices = controller.scope.devices;
    var device = null;
    var x = controller.scope.scaledX;
    var y = controller.scope.scaledY;
    var app = null;

    for(i=0; i < devices.length; i++) {
        device = devices[i];
        if (device.is_selected(x, y)) {
            console.log(device);

            app = new models.Process(device.process_id_seq(),
                                     message.process.name,
                                     message.process.type,
                                     controller.scope.scaledX,
                                     controller.scope.scaledY);
            app.device = device;
            device.processes.push(app);
            controller.scope.send_control_message(new messages.ProcessCreate(controller.scope.client_id,
                                                                             app.id,
                                                                             app.name,
                                                                             app.type,
                                                                             app.device.id,
                                                                             app.x,
                                                                             app.y));
            break;
        } else {
            console.log([x,y, device.x, device.y]);
        }
    }
};
