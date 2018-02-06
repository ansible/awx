

function scale_animation (scope) {
    var incr_s = (scope.data.new_scale - scope.data.current_scale) / scope.steps;
    scope.data.scope.current_scale = incr_s * scope.frame_number + scope.data.current_scale;
    scope.data.scope.first_channel.send("ScaleChanged", {});
    scope.data.scope.updateScaledXY();
    scope.data.scope.updatePanAndScale();
}
exports.scale_animation = scale_animation;

function pan_animation (scope) {
    var incr_x = (scope.data.x2 - scope.data.x1) / scope.steps;
    scope.data.scope.panX = incr_x * scope.frame_number + scope.data.x1;
    var incr_y = (scope.data.y2 - scope.data.y1) / scope.steps;
    scope.data.scope.panY = incr_y * scope.frame_number + scope.data.y1;
    scope.data.scope.first_channel.send("PanChanged", {});
    scope.data.scope.updateScaledXY();
    scope.data.scope.updatePanAndScale();
}
exports.pan_animation = pan_animation;
