/* Copyright (c) 2017-2018 Red Hat, Inc. */
var fsm = require('./fsm.js');
var button = require('./button.js');
var util = require('./util.js');
var inherits = require('inherits');
var animation_fsm = require('./animation.fsm.js');

function Device(id, name, x, y, type, host_id) {
    this.id = id;
    this.host_id = host_id ? host_id: 0;
    this.name = name;
    this.x = x;
    this.y = y;
    this.height = type === "host" ? 20 : 37.5;
    this.width = 37.5;
    this.size = 37.5;
    this.type = type;
    this.selected = false;
    this.remote_selected = false;
    this.edit_label = false;
    this.status = null;
    this.working = false;
    this.moving = false;
    this.icon = false;
    this.tasks = [];
    this.shape = type === "router" ? "circular" : "rectangular";
    this.interface_seq = util.natural_numbers(0);
    this.interfaces = [];
    this.process_id_seq = util.natural_numbers(0);
    this.processes = [];
    this.in_group = false;
}
exports.Device = Device;

Device.prototype.toJSON = function () {
    return {id: this.id,
            name: this.name,
            x: this.x,
            y: this.y,
            type: this.type,
            interfaces: this.interfaces.map(function (x) {
                return x.toJSON();
            }),
            processes: this.processes.map(function (x) {
                return x.toJSON();
            })};
};

Device.prototype.is_selected = function (x, y) {

    return (x > this.x - this.width &&
            x < this.x + this.width &&
            y > this.y - this.height &&
            y < this.y + this.height);

};

Device.prototype.describeArc = util.describeArc;


function Interface(id, name) {
    this.id = id;
    this.name = name;
    this.link = null;
    this.device = null;
    this.edit_label = false;
    this.dot_x = null;
    this.dot_y = null;
}
exports.Interface = Interface;

Interface.prototype.toJSON = function () {

    return {id: this.id,
            name: this.name};
};

Interface.prototype.remote_interface = function () {

    if (this.link === null) {
        return null;
    }
    if (this.link.to_interface === this) {
        return this.link.from_interface;
    } else {
        return this.link.to_interface;
    }
};

Interface.prototype.is_selected = function (x, y) {

    if (this.link === null || this.device === null) {
        return false;
    }

    var d = Math.sqrt(Math.pow(x - this.device.x, 2) + Math.pow(y - this.device.y, 2));
    return this.link.is_selected(x, y) && (d < this.dot_d + 30);
};

Interface.prototype.dot_distance = function () {
    this.dot_d = Math.sqrt(Math.pow(this.device.x - this.dot_x, 2) + Math.pow(this.device.y - this.dot_y, 2));
};

Interface.prototype.dot = function () {
    if (this.link === null || this.device === null) {
        return;
    }
    if (this.link.to_device === null || this.link.from_device === null) {
        return;
    }
    var p;
    if (this.device.shape === "circular") {

        var theta = this.link.slope_rads();
        if (this.link.from_interface === this) {
            theta = theta + Math.PI;
        }
        p = {x: this.device.x - this.device.size * Math.cos(theta),
                y: this.device.y - this.device.size * Math.sin(theta)};
        this.dot_x = p.x;
        this.dot_y = p.y;
        this.dot_distance();
        return;
    }

    var x1;
    var y1;
    var x2;
    var y2;
    var x3;
    var y3;
    var x4;
    var y4;
    var param1;
    var param2;

    x3 = this.link.to_device.x;
    y3 = this.link.to_device.y;
    x4 = this.link.from_device.x;
    y4 = this.link.from_device.y;

    x1 = this.device.x - this.device.width;
    y1 = this.device.y - this.device.height;
    x2 = this.device.x + this.device.width;
    y2 = this.device.y - this.device.height;

    p = util.intersection(x3, y3, x4, y4, x1, y1, x2, y2);
    param1 = util.pCase(p.x, p.y, x1, y1, x2, y2);
    param2 = util.pCase(p.x, p.y, x3, y3, x4, y4);
    if (param1 >= 0 && param1 <= 1 && param2 >= 0 && param2 <= 1) {
        this.dot_x = p.x;
        this.dot_y = p.y;
        this.dot_distance();
        return;
    }


    x1 = this.device.x - this.device.width;
    y1 = this.device.y + this.device.height;
    x2 = this.device.x + this.device.width;
    y2 = this.device.y + this.device.height;

    p = util.intersection(x3, y3, x4, y4, x1, y1, x2, y2);
    param1 = util.pCase(p.x, p.y, x1, y1, x2, y2);
    param2 = util.pCase(p.x, p.y, x3, y3, x4, y4);
    if (param1 >= 0 && param1 <= 1 && param2 >= 0 && param2 <= 1) {
        this.dot_x = p.x;
        this.dot_y = p.y;
        this.dot_distance();
        return;
    }

    x1 = this.device.x + this.device.width;
    y1 = this.device.y - this.device.height;
    x2 = this.device.x + this.device.width;
    y2 = this.device.y + this.device.height;

    p = util.intersection(x3, y3, x4, y4, x1, y1, x2, y2);
    param1 = util.pCase(p.x, p.y, x1, y1, x2, y2);
    param2 = util.pCase(p.x, p.y, x3, y3, x4, y4);
    if (param1 >= 0 && param1 <= 1 && param2 >= 0 && param2 <= 1) {
        this.dot_x = p.x;
        this.dot_y = p.y;
        this.dot_distance();
        return;
    }

    x1 = this.device.x - this.device.width;
    y1 = this.device.y - this.device.height;
    x2 = this.device.x - this.device.width;
    y2 = this.device.y + this.device.height;

    p = util.intersection(x3, y3, x4, y4, x1, y1, x2, y2);
    param1 = util.pCase(p.x, p.y, x1, y1, x2, y2);
    param2 = util.pCase(p.x, p.y, x3, y3, x4, y4);
    if (param1 >= 0 && param1 <= 1 && param2 >= 0 && param2 <= 1) {
        this.dot_x = p.x;
        this.dot_y = p.y;
        this.dot_distance();
        return;
    }

};

function Link(id, from_device, to_device, from_interface, to_interface) {
    this.id = id;
    this.from_device = from_device;
    this.to_device = to_device;
    this.from_interface = from_interface;
    this.to_interface = to_interface;
    this.selected = false;
    this.remote_selected = false;
    this.status = null;
    this.edit_label = false;
    this.name = "";
}
exports.Link = Link;

Link.prototype.toJSON = function () {

    return {from_device_id: this.from_device.id,
            to_device_id: this.to_device.id,
            from_interface_id: this.from_interface.id,
            to_interface_id: this.to_interface.id,
            name: this.name};
};

Link.prototype.is_selected = function (x, y) {
    // Is the distance to the mouse location less than 25 if on the label side
    // or 5 on the other from the shortest line to the link?

    if (this.to_device === null) {
        return false;
    }
    var d = util.pDistance(x,
                           y,
                           this.from_device.x,
                           this.from_device.y,
                           this.to_device.x,
                           this.to_device.y);
    if (util.cross_z_pos(x,
                         y,
                         this.from_device.x,
                         this.from_device.y,
                         this.to_device.x,
                         this.to_device.y)) {
        return d < 10;
    } else {
        return d < 10;
    }
};

Link.prototype.slope_rads = function () {
    //Return the slope in degrees for this link.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.atan2(y2 - y1, x2 - x1);
};

Link.prototype.slope = function () {
    //Return the slope in degrees for this link.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI + 180;
};

Link.prototype.pDistanceLine = function (x, y) {

    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return util.pDistanceLine(x, y, x1, y1, x2, y2);
};


Link.prototype.length = function () {
    //Return the length of this link.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.sqrt(Math.pow(x1-x2, 2) + Math.pow(y1-y2, 2));
};

Link.prototype.plength = function (x, y) {
    //Return the length of this link.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return util.pDistance(x, y, x1, y1, x2, y2);
};

function ActionIcon(name, x, y, r, callback, enabled, tracer) {
    this.name = name;
    this.x = x;
    this.y = y;
    this.r = r;
    this.callback = callback;
    this.is_pressed = false;
    this.mouse_over = false;
    this.enabled = enabled;
    this.fsm = new fsm.FSMController(this, "button_fsm", enabled ? button.Start : button.Disabled, tracer);
}
exports.ActionIcon = ActionIcon;

ActionIcon.prototype.is_selected = function (x, y) {

    return (x > this.x - this.r &&
            x < this.x + this.r &&
            y > this.y - this.r &&
            y < this.y + this.r);

};

function Button(name, x, y, width, height, callback, tracer) {
    this.name = name;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.callback = callback;
    this.is_pressed = false;
    this.mouse_over = false;
    this.enabled = true;
    this.fsm = new fsm.FSMController(this, "button_fsm", button.Start, tracer);
}
exports.Button = Button;


Button.prototype.is_selected = function (x, y) {

    return (x > this.x &&
            x < this.x + this.width &&
            y > this.y &&
            y < this.y + this.height);

};


function ToggleButton(name, x, y, width, height, toggle_callback, untoggle_callback, default_toggled, tracer) {
    this.name = name;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.callback = this.toggle;
    this.is_pressed = default_toggled;
    this.toggled = default_toggled;
    this.toggle_callback = toggle_callback;
    this.untoggle_callback = untoggle_callback;
    this.mouse_over = false;
    this.enabled = true;
    this.fsm = new fsm.FSMController(this, "button_fsm", button.Start, tracer);
}
inherits(ToggleButton, Button);
exports.ToggleButton = ToggleButton;

ToggleButton.prototype.toggle = function () {
    this.toggled = !this.toggled;
    this.is_pressed = this.toggled;

    if (this.toggled) {
        this.toggle_callback();
    } else {
        this.untoggle_callback();
    }
};

function ContextMenu(name, x, y, width, height, callback, enabled, buttons, tracer) {
    this.name = name;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.callback = callback;
    this.is_pressed = false;
    this.mouse_over = false;
    this.enabled = false;
    this.buttons = buttons;
    this.fsm = new fsm.FSMController(this, "button_fsm", enabled ? button.Start : button.Disabled, tracer);
}
exports.ContextMenu = ContextMenu;


ContextMenu.prototype.is_selected = function (x, y) {

    return (x > this.x &&
            x < this.x + this.width &&
            y > this.y &&
            y < this.y + this.height);

};

function ContextMenuButton(name, x, y, width, height, callback, tracer) {
    this.name = name;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.callback = callback;
    this.is_pressed = false;
    this.mouse_over = false;
    this.enabled = true;
    this.fsm = new fsm.FSMController(this, "button_fsm", button.Start, tracer);
}
exports.ContextMenuButton = ContextMenuButton;


ContextMenuButton.prototype.is_selected = function (x, y) {

    return (x > this.x &&
            x < this.x + this.width &&
            y > this.y &&
            y < this.y + this.height);

};


function Group(id, name, type, x1, y1, x2, y2, selected) {
    this.id = id;
    this.name = name;
    this.type = type;
    this.x1 = x1;
    this.y1 = y1;
    this.x2 = x2;
    this.y2 = y2;
    this.selected = selected;
    this.moving = false;
    this.highlighted = false;
    this.fsm = null;
    this.selected_corner = null;
    this.devices = [];
    this.links = [];
    this.groups = [];
    this.streams = [];
    this.icon_size = type === 'site' ? 500 : 100;
}
exports.Group = Group;

Group.prototype.toJSON = function () {

    return {id: this.id,
            name: this.name,
            type: this.type,
            x1: this.x1,
            y1: this.y1,
            x2: this.x2,
            y2: this.y2,
            devices: this.devices,
            links: this.links,
            streams: this.streams,
            groups: this.groups};
};


Group.prototype.update_hightlighted = function (x, y) {

    this.highlighted = this.is_highlighted(x, y);
};

Group.prototype.is_highlighted = function (x, y) {

    return (x > this.left_extent() &&
            x < this.right_extent() &&
            y > this.top_extent() &&
            y < this.bottom_extent());

};

Group.prototype.is_icon_selected = function (x, y) {

    return ((x > this.left_extent() &&
             x < this.right_extent() &&
             y > this.top_extent() &&
             y < this.bottom_extent()) ||
            (x > this.centerX() - this.icon_size &&
             x < this.centerX() + this.icon_size &&
             y > this.centerY() - this.icon_size &&
             y < this.centerY() + this.icon_size));

};

var TOP_LEFT = 0;
exports.TOP_LEFT = TOP_LEFT;
var TOP_RIGHT = 1;
exports.TOP_RIGHT = TOP_RIGHT;
var BOTTOM_LEFT = 2;
exports.BOTTOM_LEFT = BOTTOM_LEFT;
var BOTTOM_RIGHT = 3;
exports.BOTTOM_RIGHT = BOTTOM_RIGHT;

Group.prototype.has_corner_selected = function (x, y) {

    if (x > this.left_extent() &&
        x < this.left_extent() + 10 &&
        y > this.top_extent() &&
        y < this.top_extent() + 10) {
        return true;
    }
    if (x > this.left_extent() &&
        x < this.left_extent() + 10 &&
        y > this.bottom_extent() - 10 &&
        y < this.bottom_extent()) {
        return true;
    }
    if (x > this.right_extent() - 10 &&
        x < this.right_extent() &&
        y > this.bottom_extent() - 10 &&
        y < this.bottom_extent()) {
        return true;
    }
    if (x > this.right_extent() - 10 &&
        x < this.right_extent() &&
        y > this.top_extent() &&
        y < this.top_extent() + 10) {
        return true;
    }

    return false;
};

Group.prototype.select_corner = function (x, y) {

    var corners = [[util.distance(this.x1, this.y1, x, y), TOP_LEFT],
                   [util.distance(this.x2, this.y2, x, y), BOTTOM_RIGHT],
                   [util.distance(this.x1, this.y2, x, y), BOTTOM_LEFT],
                   [util.distance(this.x2, this.y1, x, y), TOP_RIGHT]];

    corners.sort(function(a, b) {
        return a[0] - b[0];
    });

    if (corners[0][0] > 30) {
        return null;
    }

    return corners[0][1];
};

Group.prototype.is_selected = function (x, y) {

    if (util.pDistance(x,
                       y,
                       this.left_extent(),
                       this.top_extent(),
                       this.left_extent(),
                       this.bottom_extent()) < 10) {
        return true;
    }
    if (util.pDistance(x,
                       y,
                       this.left_extent(),
                       this.top_extent(),
                       this.right_extent(),
                       this.top_extent()) < 10) {
        return true;
    }
    if (util.pDistance(x,
                       y,
                       this.left_extent(),
                       this.top_extent(),
                       this.right_extent(),
                       this.top_extent()) < 40 && y > this.top_extent()) {
        return true;
    }
    if (util.pDistance(x,
                       y,
                       this.right_extent(),
                       this.bottom_extent(),
                       this.right_extent(),
                       this.top_extent()) < 10) {
        return true;
    }
    if (util.pDistance(x,
                       y,
                       this.right_extent(),
                       this.bottom_extent(),
                       this.left_extent(),
                       this.bottom_extent()) < 10) {
        return true;
    }

    return false;
};

Group.prototype.width = function (scaledX) {
    var x2 = this.x2 !== null ? this.x2 : scaledX;
    return Math.abs(this.x1 - x2);
};

Group.prototype.height = function (scaledY) {
    var y2 = this.y2 !== null ? this.y2 : scaledY;
    return Math.abs(this.y1 - y2);
};

Group.prototype.top_extent = function (scaledY) {
    var y2 = this.y2 !== null ? this.y2 : scaledY;
    return (this.y1 < y2? this.y1 : y2);
};

Group.prototype.left_extent = function (scaledX) {
    var x2 = this.x2 !== null ? this.x2 : scaledX;
    return (this.x1 < x2? this.x1 : x2);
};

Group.prototype.bottom_extent = function (scaledY) {
    var y2 = this.y2 !== null ? this.y2 : scaledY;
    return (this.y1 > y2? this.y1 : y2);
};

Group.prototype.right_extent = function (scaledX) {
    var x2 = this.x2 !== null ? this.x2 : scaledX;
    return (this.x1 > x2? this.x1 : x2);
};

Group.prototype.centerX = function (scaledX) {
    return (this.right_extent(scaledX) + this.left_extent(scaledX)) / 2;
};

Group.prototype.centerY = function (scaledY) {
    return (this.bottom_extent(scaledY) + this.top_extent(scaledY)) / 2;
};

Group.prototype.update_membership = function (devices, groups) {
    var i = 0;
    var y1 = this.top_extent();
    var x1 = this.left_extent();
    var y2 = this.bottom_extent();
    var x2 = this.right_extent();
    var old_devices = this.devices;
    var device_ids = [];
    this.devices = [];
    for (i = 0; i < devices.length; i++) {
        if (devices[i].x > x1 &&
            devices[i].y > y1 &&
            devices[i].x < x2 &&
            devices[i].y < y2) {
            devices[i].in_group = true;
            this.devices.push(devices[i]);
            device_ids.push(devices[i].id);
        }
    }
    var old_groups = this.groups;
    this.groups = [];
    var group_ids = [];
    for (i = 0; i < groups.length; i++) {
        if (groups[i].left_extent() > x1 &&
            groups[i].top_extent() > y1 &&
            groups[i].right_extent() < x2 &&
            groups[i].bottom_extent() < y2) {
            this.groups.push(groups[i]);
            group_ids.push(groups[i].id);
        }
    }
    return [old_devices, this.devices, device_ids, old_groups, this.groups, group_ids];
};


function ToolBox(id, name, type, x, y, width, height) {
    this.id = id;
    this.name = name;
    this.type = type;
    this.x = x;
    this.y = y;
    this.width = width;
    this.height = height;
    this.items = [];
    this.spacing = 200;
    this.scroll_offset = 0;
    this.selected_item = null;
    this.enabled = true;
}
exports.ToolBox = ToolBox;


function Process(id, name, type, x, y) {
    this.id = id;
    this.name = name;
    this.type = type;
    this.x = x;
    this.y = y;
    this.height = 50;
    this.width = 50;
    this.size = 50;
    this.selected = null;
    this.enabled = true;
    this.icon = false;
    this.device = null;
}
exports.Process = Process;

Process.prototype.toJSON = function () {
    return {id: this.id,
            name: this.name};
};

function Stream(id, from_device, to_device, label) {
    this.id = id;
    this.from_device = from_device;
    this.to_device = to_device;
    this.selected = false;
    this.remote_selected = false;
    this.label = label;
    this.offset = 0;
}
exports.Stream = Stream;

Stream.prototype.toJSON = function () {
    return {to_device: this.to_device.id,
            from_device: this.from_device.id};
};

Stream.prototype.slope_rad = function () {
    //Return the slope in radians for this transition.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.atan2(y2 - y1, x2 - x1) + Math.PI;
};

Stream.prototype.slope = function () {
    //Return the slope in degrees for this transition.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI + 180;
};

Stream.prototype.flip_text_rotate = function () {
    var slope = this.slope();
    if (slope > 90 && slope < 270) {
        return 180;
    } else {
        return 0;
    }
};

Stream.prototype.flip_text_offset = function () {
    var slope = this.slope();
    if (slope > 90 && slope < 270) {
        return 10;
    } else {
        return 0;
    }
};

Stream.prototype.pslope = function () {
    //Return the slope of a perpendicular line to this
    //transition
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    var slope = (y2 - y1)/(x2 - x1);
    //var intercept = - slope * x1;
    var pslope = 1/slope;
    return Math.atan(pslope)  * 180 / Math.PI + 180;
};

Stream.prototype.perpendicular = function (x, y) {
    //Find the perpendicular line through x, y to this transition.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    var slope = (y2 - y1)/(x2 - x1);
    var intercept = y1 - slope * x1;
    var pslope = -1/slope;
    var pintercept = y - pslope * x;

    var xi = (pintercept - intercept) / (slope - pslope);
    var yi = pslope * xi + pintercept;
    return {x1:x, y1:y, x2: xi, y2: yi};
};

Stream.prototype.is_selected = function (x, y) {
    // Is the distance to the mouse location less than 25 if on the label side
    // or 5 on the other from the shortest line to the transition?
    console.log("is_selected");
    var phi = this.slope_rad();
    console.log({"phi": phi});
    console.log({'x': this.from_device.x, 'y': this.from_device.y});
    console.log({'x': this.to_device.x, 'y': this.to_device.y});
    console.log({'x': x, 'y': y});
    var p1 = util.cartesianToPolar(this.from_device.x, this.from_device.y);
    var p2 = util.cartesianToPolar(this.to_device.x, this.to_device.y);
    var p3 = util.cartesianToPolar(x, y);
    console.log(p1);
    p1.theta -= phi;
    console.log(p1);
    console.log(p2);
    p2.theta -= phi;
    console.log(p2);
    p3.theta -= phi;

    p1 = util.polarToCartesian_rad(0, 0, p1.r, p1.theta);
    p2 = util.polarToCartesian_rad(0, 0, p2.r, p2.theta);
    p3 = util.polarToCartesian_rad(0, 0, p3.r, p3.theta);
    p2.y -= this.arc_offset2();
    console.log(p1);
    console.log(p2);
    console.log(p3);
    var max_x = Math.max(p1.x, p2.x);
    var min_x = Math.min(p1.x, p2.x);
    var max_y = Math.max(p1.y, p2.y) + 5;
    var min_y = Math.min(p1.y, p2.y) - 25 ;

    return p3.x > min_x && p3.x < max_x && p3.y > min_y && p3.y < max_y;
};

Stream.prototype.length = function () {
    //Return the length of this transition.
    var x1 = this.from_device.x;
    var y1 = this.from_device.y;
    var x2 = this.to_device.x;
    var y2 = this.to_device.y;
    return Math.sqrt(Math.pow(x1-x2, 2) + Math.pow(y1-y2, 2));
};


Stream.prototype.inter_length = function () {
    //Return the length of this transition between states.
    return this.length() - this.from_device.size - this.to_device.size;
};

Stream.prototype.arc_r = function () {
    return this.inter_length();
};

Stream.prototype.arc_r2 = function () {
    var offset_to_r = [2, 1, 0.75, 0.6, 0.55, 0.53, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5];
    return this.length() * offset_to_r[this.offset];
};

Stream.prototype.arc_offset = function () {
    var r = this.arc_r();
    var offset =  r - (Math.sin(this.arc_angle_rad()) * r);
    return offset;
};

Stream.prototype.arc_offset2 = function () {
    var r = this.arc_r2();
    var theta = Math.acos((this.length() / 2) / r);
    var offset =  r * (1 - Math.sin(theta));
    return offset;
};

Stream.prototype.arc_angle_rad = function () {
    return Math.acos((this.inter_length() / 2) / this.arc_r());
};

Stream.prototype.arc_angle_tan_rad = function () {
    return Math.PI/2 - Math.acos((this.inter_length() / 2) / this.arc_r());
};

Stream.prototype.arc_angle_tan = function () {
    return this.arc_angle_tan_rad() * 180 / Math.PI;
};

Stream.prototype.arc_angle_tan_rad2 = function () {
    var r = this.arc_r2();
    var l = this.length();
    var phi = this.end_arc_angle_rad();
    return Math.PI/2 - Math.acos((l/2 - Math.cos(phi) * this.to_device.size) / r);
};

Stream.prototype.arc_angle_tan2 = function () {
    return this.arc_angle_tan_rad2() * 180 / Math.PI;
};

Stream.prototype.end_arc_angle_rad = function () {
    var r = this.arc_r2();
    var l = this.length();
    return Math.acos((this.to_device.size / 2) / r) - Math.acos((l/2)/r);
};

Stream.prototype.end_arc_angle = function () {
    return this.end_arc_angle_rad() * 180 / Math.PI;
};

Stream.prototype.start_arc_angle_rad = function () {
    return Math.acos((this.from_device.size / 2) / this.arc_r2()) - Math.acos((this.length()/2)/this.arc_r2());
};

Stream.prototype.start_arc_angle = function () {
    return this.start_arc_angle_rad() * 180 / Math.PI;
};

function Test(name, event_trace, fsm_trace, pre_test_snapshot, post_test_snapshot) {
    this.name = name;
    this.event_trace = event_trace;
    this.fsm_trace = fsm_trace;
    this.pre_test_snapshot = pre_test_snapshot;
    this.post_test_snapshot = post_test_snapshot;
}
exports.Test = Test;

function TestResult(id, name, result, date, code_under_test) {
    this.id = id;
    this.name = name;
    this.result = result;
    this.date = date;
    this.code_under_test = code_under_test;
}
exports.TestResult = TestResult;

function Animation(id, steps, data, scope, tracer, callback) {

    this.id = id;
    this.steps = steps;
    this.active = true;
    this.frame_number_seq = util.natural_numbers(-1);
    this.frame_number = 0;
    this.data = data;
    this.data.updateZoomBoolean = data.updateZoomBoolean !== undefined ? data.updateZoomBoolean : true;
    this.callback = callback;
    this.scope = scope;
    this.interval = null;
    this.fsm = new fsm.FSMController(this, "animation_fsm", animation_fsm.Start, tracer);
}
exports.Animation = Animation;
