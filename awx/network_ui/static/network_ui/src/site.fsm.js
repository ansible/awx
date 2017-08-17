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
