var inherits = require('inherits');
var fsm = require('./fsm.js');

function _State () {
}
inherits(_State, fsm._State);

function _Ready () {
    this.name = 'Ready';
}
inherits(_Ready, _State);
var Ready = new _Ready();
exports.Ready = Ready;

function _Start () {
    this.name = 'Start';
}
inherits(_Start, _State);
var Start = new _Start();
exports.Start = Start;

function _Scale () {
    this.name = 'Scale';
}
inherits(_Scale, _State);
var Scale = new _Scale();
exports.Scale = Scale;

function _Pressed () {
    this.name = 'Pressed';
}
inherits(_Pressed, _State);
var Pressed = new _Pressed();
exports.Pressed = Pressed;

function _Pan () {
    this.name = 'Pan';
}
inherits(_Pan, _State);
var Pan = new _Pan();
exports.Pan = Pan;




_Ready.prototype.onMouseDown = function (controller) {

    controller.scope.pressedX = controller.scope.mouseX;
    controller.scope.pressedY = controller.scope.mouseY;
    controller.scope.lastPanX = controller.scope.panX;
    controller.scope.lastPanY = controller.scope.panY;
    controller.changeState(Pressed);

};

_Ready.prototype.onTouchStart = function (controller, msg_type, event) {

    if (event.touches.length === 2) {

        controller.scope.lastPanX = controller.scope.panX;
        controller.scope.lastPanY = controller.scope.panY;
        controller.scope.lastScale = controller.scope.current_scale;

        var x1 = event.touches[0].screenX;
        var y1 = event.touches[0].screenY;
        var x2 = event.touches[1].screenX;
        var y2 = event.touches[1].screenY;
        var d = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        var xb = (x2 + x1) / 2;
        var yb = (y2 + y1) / 2;

        controller.scope.touch_data = {x1: x1,
                                    y1: y1,
                                    x2: x2,
                                    y2: y2,
                                    d: d,
                                    xb: xb,
                                    yb: yb};
        controller.changeState(Pressed);
    }
};

_Ready.prototype.onMouseWheel = function (controller, msg_type, $event) {

    controller.changeState(Scale);
    controller.handle_message(msg_type, $event);
};


_Start.prototype.start = function (controller) {

    controller.changeState(Ready);

};

_Scale.prototype.onMouseWheel = function (controller, msg_type, message) {
      var delta = message[1];
      var new_scale = Math.max(0.1, Math.min(10, (controller.scope.current_scale + delta / 100)));
      var new_panX = controller.scope.mouseX - new_scale * ((controller.scope.mouseX - controller.scope.panX) / controller.scope.current_scale);
      var new_panY = controller.scope.mouseY - new_scale * ((controller.scope.mouseY - controller.scope.panY) / controller.scope.current_scale);
      controller.scope.updateScaledXY();
      controller.scope.current_scale = new_scale;
      controller.scope.panX = new_panX;
      controller.scope.panY = new_panY;
      controller.scope.updatePanAndScale();
      controller.changeState(Ready);
};
_Scale.prototype.onMouseWheel.transitions = ['Ready'];


_Pressed.prototype.onMouseUp = function (controller) {

    controller.changeState(Ready);

};
_Pressed.prototype.onMouseUp.transitions = ['Ready'];

_Pressed.prototype.onTouchEnd = _Pressed.prototype.onMouseUp;

_Pressed.prototype.onMouseMove = function (controller, msg_type, $event) {

    controller.changeState(Pan);
    controller.handle_message(msg_type, $event);
};
_Pressed.prototype.onMouseMove.transitions = ['Pan'];

_Pressed.prototype.onTouchMove = _Pressed.prototype.onMouseMove;

_Pan.prototype.onMouseMove = function (controller) {

    controller.scope.panX = (controller.scope.mouseX - controller.scope.pressedX) + controller.scope.lastPanX;
    controller.scope.panY = (controller.scope.mouseY - controller.scope.pressedY) + controller.scope.lastPanY;
    controller.scope.updateScaledXY();
    controller.scope.updatePanAndScale();
};

_Pan.prototype.onTouchMove = function (controller, msg_type, event) {


    if (event.touches.length === 2) {
        var x1 = event.touches[0].screenX;
        var y1 = event.touches[0].screenY;
        var x2 = event.touches[1].screenX;
        var y2 = event.touches[1].screenY;
        var d = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
        var xb = (x2 + x1) / 2;
        var yb = (y2 + y1) / 2;
        var delta = d - controller.scope.touch_data.d;

        controller.scope.panX = (xb - controller.scope.touch_data.xb) + controller.scope.lastPanX;
        controller.scope.panY = (yb - controller.scope.touch_data.yb) + controller.scope.lastPanY;
        controller.scope.updateScaledXY();

        var new_scale = Math.max(0.1, Math.min(10, (controller.scope.lastScale + delta / 100)));
        var new_panX = xb - new_scale * ((xb - controller.scope.panX) / controller.scope.lastScale);
        var new_panY = yb - new_scale * ((yb - controller.scope.panY) / controller.scope.lastScale);
        controller.scope.current_scale = new_scale;
        controller.scope.panX = new_panX;
        controller.scope.panY = new_panY;
        controller.scope.updatePanAndScale();
    }
};


_Pan.prototype.onMouseUp = function (controller) {

    controller.changeState(Ready);

};
_Pan.prototype.onMouseUp.transitions = ['Ready'];

_Pan.prototype.onTouchEnd = _Pan.prototype.onMouseUp;
