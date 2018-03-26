var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);


function _Disabled () {
    this.name = 'Disabled';
}
inherits(_Disabled, _State);
var Disabled = new _Disabled();
exports.Disabled = Disabled;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Enabled () {
    this.name = 'Enabled';
}
inherits(_Enabled, _State);
var Enabled = new _Enabled();
exports.Enabled = Enabled;




_Disabled.prototype.onBindDocument = function (controller) {

    $(document).bind("keydown", controller.scope.onKeyDown);
    controller.changeState(Enabled);

};
_Disabled.prototype.onBindDocument.transitions = ['Enabled'];



_Start.prototype.start = function (controller) {

    $(document).bind("keydown", controller.scope.onKeyDown);
    controller.changeState(Enabled);

};
_Start.prototype.start.transitions = ['Enabled'];



_Enabled.prototype.onUnbindDocument = function (controller) {

    $(document).unbind("keydown", controller.scope.onKeyDown);
    controller.changeState(Disabled);

};
_Enabled.prototype.onUnbindDocument.transitions = ['Disabled'];

_Disabled.prototype.onDetailsPanelClose = function (controller) {

    $(document).bind("keydown", controller.scope.onKeyDown);
    controller.changeState(Enabled);

};
_Disabled.prototype.onDetailsPanelClose.transitions = ['Enabled'];

_Disabled.prototype.onSearchDropdownClose = function (controller) {

    $(document).bind("keydown", controller.scope.onKeyDown);
    controller.changeState(Enabled);

};
_Disabled.prototype.onSearchDropdownClose.transitions = ['Enabled'];



_Enabled.prototype.onDetailsPanel = function (controller) {

    $(document).unbind("keydown", controller.scope.onKeyDown);
    controller.changeState(Disabled);

};
_Enabled.prototype.onDetailsPanel.transitions = ['Disabled'];

_Enabled.prototype.onSearchDropdown = function (controller) {

    $(document).unbind("keydown", controller.scope.onKeyDown);
    controller.changeState(Disabled);

};
_Enabled.prototype.onSearchDropdown.transitions = ['Disabled'];
