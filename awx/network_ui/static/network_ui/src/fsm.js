/* Copyright (c) 2017 Red Hat, Inc. */
function FSMController (scope, initial_state, next_controller) {
    this.scope = scope;
    this.state = initial_state;
    this.state.start(this);
    this.next_controller = next_controller;
}
exports.FSMController = FSMController;

FSMController.prototype.changeState = function (state) {
    if(this.state !== null) {
        this.state.end(this);
    }
    this.state = state;
    if(state !== null) {
        state.start(this);
    }
};

FSMController.prototype.handle_message = function(msg_type, message) {

    var handler_name = 'on' + msg_type;
    if (typeof(this.state[handler_name]) !== "undefined") {
        this.state[handler_name](this, msg_type, message);
    } else {
        this.default_handler(msg_type, message);
    }
};

FSMController.prototype.default_handler = function(msg_type, message) {
    if (this.next_controller !== null) {
        this.next_controller.handle_message(msg_type, message);
    }
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
