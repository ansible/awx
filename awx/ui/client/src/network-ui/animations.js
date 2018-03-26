
function scale_animation (scope) {

    var initial_height = ((1 / scope.data.current_scale) - 1);
    var height = (scope.data.end_height - initial_height) * (scope.frame_number / scope.steps) + initial_height;
    scope.data.scope.current_scale = 1 / (1 + height);
    scope.data.scope.updatePanAndScale();
    scope.data.scope.$emit('awxNet-UpdateZoomWidget', scope.data.scope.current_scale, scope.data.updateZoomBoolean);
}
exports.scale_animation = scale_animation;

function pan_animation (scope) {
    var incr_x = (scope.data.x2 - scope.data.x1) / scope.steps;
    var incr_y = (scope.data.y2 - scope.data.y1) / scope.steps;
    var v_x = incr_x * scope.frame_number + scope.data.x1;
    var v_y = incr_y * scope.frame_number + scope.data.y1;
    var p = scope.data.scope.to_pan(v_x, v_y);
    scope.data.scope.panX = p.x + scope.data.scope.graph.width/2;
    scope.data.scope.panY = p.y + scope.data.scope.graph.height/2;
    scope.data.scope.first_channel.send("PanChanged", {});
    scope.data.scope.updatePanAndScale();
}
exports.pan_animation = pan_animation;
