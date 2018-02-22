var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Collapsed () {
    this.name = 'Collapsed';
}
inherits(_Collapsed, _State);
var Collapsed = new _Collapsed();
exports.Collapsed = Collapsed;

function _Expanded () {
    this.name = 'Expanded';
}
inherits(_Expanded, _State);
var Expanded = new _Expanded();
exports.Expanded = Expanded;




_Start.prototype.start = function (controller, msg_type, $event) {

    controller.scope.$parent.vm.rightPanelIsExpanded = false;
    controller.changeState(Collapsed);
    controller.handle_message(msg_type, $event);

};
_Start.prototype.start.transitions = ['Collapsed'];



_Collapsed.prototype.onDetailsPanel = function (controller, msg_type, $event) {

    controller.scope.$parent.vm.rightPanelIsExpanded = true;
    controller.changeState(Expanded);
    controller.handle_message(msg_type, $event);

};
_Collapsed.prototype.onDetailsPanel.transitions = ['Expanded'];



_Expanded.prototype.onDetailsPanelClose = function (controller, msg_type, $event) {

    controller.scope.$parent.vm.rightPanelIsExpanded = false;
    controller.scope.$parent.vm.keyPanelExpanded = false;
    controller.changeState(Collapsed);
    controller.handle_message(msg_type, $event);
};
_Expanded.prototype.onDetailsPanelClose.transitions = ['Collapsed'];
