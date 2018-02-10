
/*
 * Uses y = cx^2 * cdx to calculate the height of the camera
 * Uses scale = 1 / (height + 1) to calculate the scale of the virtual canvas
 */

function scale_animation (scope) {
    var d = scope.steps;
    var c = scope.data.c;
    var x = scope.frame_number;
    var initial_height = (1 / scope.data.current_scale) - 1;
    var a = -1 * initial_height / (c * d);
    var height = (x + a) * (x - d) * c + scope.data.end_height;
    //console.log({x: x,
    //             c: c,
    //             d: d,
    //             a: a,
    //             h: height,
    //             i: initial_height});
    scope.data.scope.current_scale = 1 / (1 + height);
    //console.log(scope.data.scope.current_scale);
    //scope.data.scope.current_scale = 1.0;
    scope.data.scope.first_channel.send("ScaleChanged", {});
    scope.data.scope.first_channel.send("ScaleChanged", {});
    scope.data.scope.updatePanAndScale();
}
exports.scale_animation = scale_animation;

function pan_animation (scope) {
    var incr_x = (scope.data.x2 - scope.data.x1) / scope.steps;
    var incr_y = (scope.data.y2 - scope.data.y1) / scope.steps;
    //console.log({incr_x: incr_x, incr_y: incr_y});
    var v_x = incr_x * scope.frame_number + scope.data.x1;
    var v_y = incr_y * scope.frame_number + scope.data.y1;
    var p = scope.data.scope.to_pan(v_x, v_y);
    //console.log({v_x: v_x, v_y: v_y});
    //console.log({p_x: p.x, p_y: p.y});
    //scope.data.scope.panX = scope.data.scope.graph.width/2 - scope.data.scope.current_scale * p.x / 1.0;
    //scope.data.scope.panY = scope.data.scope.graph.height/2 - scope.data.scope.current_scale * p.y / 1.0;
    scope.data.scope.panX = p.x + scope.data.scope.graph.width/2;
    scope.data.scope.panY = p.y + scope.data.scope.graph.height/2;
    scope.data.scope.first_channel.send("PanChanged", {});
    scope.data.scope.updatePanAndScale();
}
exports.pan_animation = pan_animation;
