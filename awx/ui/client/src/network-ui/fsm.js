/* Copyright (c) 2017 Red Hat, Inc. */
var messages = require('./messages.js');

function Channel(from_controller, to_controller, tracer) {
    this.tracer = tracer;
    this.from_controller = from_controller;
    this.to_controller = to_controller;
    this.trace = false;
}
exports.Channel = Channel;

Channel.prototype.send = function(msg_type, message) {
    this.to_controller.handle_message(msg_type, message);
};

function NullChannel(from_controller, tracer) {
    this.tracer = tracer;
    this.from_controller = from_controller;
    this.trace = false;
}

NullChannel.prototype.send = function(msg_type) {
};

function FSMController (scope, name, initial_state, tracer) {
    this.scope = scope;
    this.name = name;
    this.state = initial_state;
    this.delegate_channel = new NullChannel(this, tracer);
    this.tracer = tracer;
    this.trace = true;
    this.handling_message_type = 'start';
    this.state.start(this);
    this.handling_message_type = null;
}
exports.FSMController = FSMController;

FSMController.prototype.changeState = function (state) {
    var old_handling_message_type;
    if(this.state !== null) {
        old_handling_message_type = this.handling_message_type;
        this.handling_message_type = 'end';
        this.state.end(this);
        this.handling_message_type = old_handling_message_type;
    }
    if (this.trace) {
        this.tracer.send_trace_message(new messages.FSMTrace(this.tracer.trace_order_seq(),
                                                             this.name,
                                                             this.state.name,
                                                             state.name,
                                                             this.handling_message_type));
    }
    this.state = state;
    if(state !== null) {
        old_handling_message_type = this.handling_message_type;
        this.handling_message_type = 'start';
        state.start(this);
        this.handling_message_type = old_handling_message_type;
    }
};

FSMController.prototype.handle_message = function(msg_type, message) {

    var old_handling_message_type = this.handling_message_type;
    this.handling_message_type = msg_type;
    var handler_name = 'on' + msg_type;
    if (typeof(this.state[handler_name]) !== "undefined") {
        this.state[handler_name](this, msg_type, message);
    } else {
        this.default_handler(msg_type, message);
    }
    this.handling_message_type = old_handling_message_type;
};

FSMController.prototype.default_handler = function(msg_type, message) {
    this.delegate_channel.send(msg_type, message);
};

function _State () {
}

_State.prototype.start = function () {
};

_State.prototype.end = function () {
};

var State = new _State();
exports.State = State;
exports._State = _State;
