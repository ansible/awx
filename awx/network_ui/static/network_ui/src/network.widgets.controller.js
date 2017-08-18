// This is not production code.   It is a development environment for UI widgets.
// Do not refactor this code with the production code in network.ui.controller.js
// This code is separate so that it can be broken without breaking the main UI code.
//console.log = function () { };
var angular = require('angular');
var fsm = require('./fsm.js');
var null_fsm = require('./null.fsm.js');
var mode_fsm = require('./mode.fsm.js');
var device_detail_fsm = require('./device.detail.fsm.js');
var rack_fsm = require('./rack.fsm.js');
var site_fsm = require('./site.fsm.js');
var hotkeys = require('./hotkeys.fsm.js');
var toolbox_fsm = require('./toolbox.fsm.js');
var view = require('./view.js');
var move = require('./move.js');
var link = require('./link.js');
var stream_fsm = require('./stream.fsm.js');
var group = require('./group.js');
var buttons = require('./buttons.js');
var time = require('./time.js');
var util = require('./util.js');
var models = require('./models.js');
var messages = require('./messages.js');
var svg_crowbar = require('./svg-crowbar.js');

var NetworkWidgetsController = function($scope, $document, $location, $window) {

  window.scope = $scope;
  var i = 0;

  $scope.topology_id = 0;

  $scope.control_socket = {
      on_message: util.noop
  };
  $scope.history = [];
  $scope.client_id = 1;
  $scope.onMouseDownResult = "";
  $scope.onMouseUpResult = "";
  $scope.onMouseEnterResult = "";
  $scope.onMouseLeaveResult = "";
  $scope.onMouseMoveResult = "";
  $scope.current_scale = 1.01;
  $scope.current_mode = null;
  $scope.current_location = [];
  $scope.panX = 100;
  $scope.panY = 100;
  $scope.mouseX = 0;
  $scope.mouseY = 0;
  $scope.scaledX = 0;
  $scope.scaledY = 0;
  $scope.pressedX = 0;
  $scope.pressedY = 0;
  $scope.pressedScaledX = 0;
  $scope.pressedScaledY = 0;
  $scope.lastPanX = 0;
  $scope.lastPanY = 0;
  $scope.selected_devices = [];
  $scope.selected_links = [];
  $scope.selected_interfaces = [];
  $scope.selected_items = [];
  $scope.selected_groups = [];
  $scope.new_link = null;
  $scope.new_stream = null;
  $scope.new_group_type = null;

  $scope.last_key = "";
  $scope.last_key_code = null;
  $scope.last_event = null;
  $scope.cursor = {'x':100, 'y': 100, 'hidden': false};

  $scope.debug = {'hidden': true};
  $scope.hide_buttons = false;
  $scope.hide_links = false;
  $scope.hide_interfaces = false;
  $scope.hide_groups = false;
  $scope.graph = {'width': window.innerWidth,
                  'right_column': window.innerWidth - 300,
                  'height': window.innerHeight};
  $scope.device_id_seq = util.natural_numbers(0);
  $scope.link_id_seq = util.natural_numbers(0);
  $scope.group_id_seq = util.natural_numbers(0);
  $scope.message_id_seq = util.natural_numbers(0);
  $scope.stream_id_seq = util.natural_numbers(0);
  $scope.time_pointer = -1;
  $scope.frame = 0;
  $scope.recording = false;
  $scope.replay = false;
  $scope.touch_data = {};
  $scope.touches = [];
  $scope.devices = [];
  $scope.stencils = [];
  $scope.links = [];
  $scope.groups = [];
  $scope.processes = [];
  $scope.configurations = [];
  $scope.streams = [];
  $scope.view_port = {'x': 0,
                      'y': 0,
                      'width': 0,
                      'height': 0};


  $scope.null_controller = new fsm.FSMController($scope, null_fsm.Start, null);
  $scope.hotkeys_controller = new fsm.FSMController($scope, hotkeys.Start, $scope.null_controller);
  $scope.view_controller = new fsm.FSMController($scope, view.Start, $scope.hotkeys_controller);
  $scope.device_detail_controller = new fsm.FSMController($scope, device_detail_fsm.Start, $scope.view_controller);
  $scope.move_controller = new fsm.FSMController($scope, move.Start, $scope.device_detail_controller);
  $scope.link_controller = new fsm.FSMController($scope, link.Start, $scope.move_controller);
  $scope.stream_controller = new fsm.FSMController($scope, stream_fsm.Start, $scope.link_controller);
  $scope.group_controller = new fsm.FSMController($scope, group.Start, $scope.stream_controller);
  $scope.rack_controller = new fsm.FSMController($scope, rack_fsm.Disable, $scope.group_controller);
  $scope.site_controller = new fsm.FSMController($scope, site_fsm.Disable, $scope.rack_controller);
  $scope.buttons_controller = new fsm.FSMController($scope, buttons.Start, $scope.site_controller);
  $scope.time_controller = new fsm.FSMController($scope, time.Start, $scope.buttons_controller);
  $scope.app_toolbox_controller = new fsm.FSMController($scope, toolbox_fsm.Start, $scope.time_controller);
  //App Toolbox Setup
  $scope.app_toolbox = new models.ToolBox(0, 'Application', 'app', 10, 200, 150, $scope.graph.height - 200 - 100);
  $scope.app_toolbox.spacing = 150;
  $scope.app_toolbox.enabled = false;
  $scope.app_toolbox_controller.toolbox = $scope.app_toolbox;
  $scope.app_toolbox_controller.dropped_action = function (selected_item) {
    $scope.first_controller.handle_message("PasteProcess", new messages.PasteProcess(selected_item));
  };
  $scope.app_toolbox.items.push(new models.Application(0, 'BGP', 'process', 0, 0));
  $scope.app_toolbox.items.push(new models.Application(0, 'OSPF', 'process', 0, 0));
  $scope.app_toolbox.items.push(new models.Application(0, 'STP', 'process', 0, 0));
  $scope.app_toolbox.items.push(new models.Application(0, 'Zero Pipeline', 'process', 0, 0));

  for(i = 0; i < $scope.app_toolbox.items.length; i++) {
      $scope.app_toolbox.items[i].icon = true;
  }

  $scope.inventory_toolbox_controller = new fsm.FSMController($scope, toolbox_fsm.Start, $scope.app_toolbox_controller);

  //Inventory Toolbox Setup
  $scope.inventory_toolbox = new models.ToolBox(0, 'Inventory', 'device', 10, 200, 150, $scope.graph.height - 200 - 100);
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router6', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Switch6', 0, 0, 'switch'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Host6', 0, 0, 'host'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router7', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router8', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router9', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router10', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router11', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router12', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router13', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router14', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router15', 0, 0, 'router'));
  $scope.inventory_toolbox.items.push(new models.Device(0, 'Router16', 0, 0, 'router'));
  $scope.inventory_toolbox.spacing = 150;
  $scope.inventory_toolbox.enabled = true;
  $scope.inventory_toolbox_controller.toolbox = $scope.inventory_toolbox;
  $scope.inventory_toolbox_controller.remove_on_drop = true;
  $scope.inventory_toolbox_controller.dropped_action = function (selected_item) {
    $scope.first_controller.handle_message("PasteDevice", new messages.PasteDevice(selected_item));
  };

  for(i = 0; i < $scope.inventory_toolbox.items.length; i++) {
      $scope.inventory_toolbox.items[i].icon = true;
  }
  //End Inventory Toolbox Setup
  $scope.rack_toolbox_controller = new fsm.FSMController($scope, toolbox_fsm.Start, $scope.inventory_toolbox_controller);
  //Rack Toolbox Setup
  $scope.rack_toolbox = new models.ToolBox(0, 'Rack', 'rack', 10, 200, 150, $scope.graph.height - 200 - 100);
  $scope.rack_toolbox.items.push(new models.Group(0, 'Rack3', 'rack', 0, 0, 200, 1000, 'false'));
  $scope.rack_toolbox.spacing = 200;
  $scope.rack_toolbox.enabled = false;
  $scope.rack_toolbox_controller.remove_on_drop = false;
  $scope.rack_toolbox_controller.toolbox = $scope.rack_toolbox;
  $scope.rack_toolbox_controller.dropped_action = function (selected_item) {
    $scope.first_controller.handle_message("PasteRack", new messages.PasteRack(selected_item));
  };
  for(i = 0; i < $scope.rack_toolbox.items.length; i++) {
      $scope.rack_toolbox.items[i].icon = true;
      $scope.rack_toolbox.items[i].selected = false;
  }
  //End Rack Toolbox Setup
  $scope.site_toolbox_controller = new fsm.FSMController($scope, toolbox_fsm.Start, $scope.rack_toolbox_controller);
  //Site Toolbox Setup
  $scope.site_toolbox = new models.ToolBox(0, 'Sites', 'sites', 10, 200, 150, $scope.graph.height - 200 - 100);
  $scope.site_toolbox.items.push(new models.Group(0, 'Site3', 'site', 0, 0, 1000, 1000, 'false'));
  $scope.site_toolbox.spacing = 200;
  $scope.site_toolbox.enabled = false;
  $scope.site_toolbox_controller.remove_on_drop = false;
  $scope.site_toolbox_controller.toolbox = $scope.site_toolbox;
  $scope.site_toolbox_controller.dropped_action = function (selected_item) {
    $scope.first_controller.handle_message("PasteSite", new messages.PasteSite(selected_item));
  };
  for(i = 0; i < $scope.site_toolbox.items.length; i++) {
      $scope.site_toolbox.items[i].icon = true;
      $scope.site_toolbox.items[i].selected = false;
  }
  //End Site Toolbox Setup

  $scope.mode_controller = new fsm.FSMController($scope, mode_fsm.Start, $scope.site_toolbox_controller);
  $scope.first_controller = $scope.mode_controller;

  var dids = $scope.device_id_seq;
  var mids = $scope.message_id_seq;
  var gids = $scope.group_id_seq;
  var lids = $scope.link_id_seq;


  $scope.initial_messages = [
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":100,"name":"Router1","type":"router","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":300,"y":100,"name":"Switch1","type":"switch","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":500,"y":100,"name":"HostA","type":"host","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":700,"y":100,"name":"Host1","type":"host","message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":300,"name":"Router2","type":"router","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":500,"name":"Router3","type":"router","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":5,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":6,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":5,"to_device_id":6,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":300,"y":300,"name":"Switch2","type":"switch","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":300,"y":500,"name":"Switch3","type":"switch","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":7,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":8,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":7,"to_device_id":8,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":500,"y":300,"name":"HostB","type":"host","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":500,"y":500,"name":"HostC","type":"host","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":9,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":10,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":9,"to_device_id":10,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":700,"y":300,"name":"Host2","type":"host","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":700,"y":500,"name":"Host3","type":"host","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":11,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":12,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":11,"to_device_id":12,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":700,"name":"Router4","type":"router","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":300,"y":700,"name":"Switch4","type":"switch","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":500,"y":700,"name":"HostD","type":"host","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":700,"y":700,"name":"Host4","type":"host","message_id":mids()}],

      ["GroupCreate",{"msg_type":"GroupCreate","sender":0,"ids":gids(),"x1":0,"y1":600,"x2":1000,"y2":800,"name":"Group1",type:"group", "message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":900,"name":"Router5","type":"router","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":300,"y":900,"name":"Switch5","type":"switch","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":500,"y":900,"name":"HostE","type":"host","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":700,"y":900,"name":"Host5","type":"host","message_id":mids()}],

      ["GroupCreate",{"msg_type":"GroupCreate","sender":0,"ids":gids(),"x1":-100,"y1":0,"x2":1100,"y2":1100,"name":"Site1",type:"site", "message_id":mids()}],
      ["GroupCreate",{"msg_type":"GroupCreate","sender":0,"ids":gids(),"x1":0,"y1":800,"x2":1000,"y2":1000,"name":"Rack1",type:"rack", "message_id":mids()}],


      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":900,"y":100,"name":"Device1","type":"device","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":900,"y":300,"name":"Device2","type":"device","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":900,"y":500,"name":"Device3","type":"device","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":22,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":23,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":22,"to_device_id":23,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":900,"y":700,"name":"Device4","type":"device","message_id":mids()}],
      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":900,"y":900,"name":"Device5","type":"device","message_id":mids()}],

      ["DeviceCreate",{"msg_type":"DeviceCreate","sender":0,"id":dids(),"x":100,"y":2900,"name":"Router6","type":"router","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":17,"id":1,"name":"eth1","message_id":mids()}],
      ["InterfaceCreate", {"msg_type":"InterfaceCreate","sender":0,"device_id":26,"id":1,"name":"eth1","message_id":mids()}],
      ["LinkCreate", {"msg_type":"LinkCreate","id":lids(),"sender":0,"name":"","from_device_id":17,"to_device_id":26,"from_interface_id":1,"to_interface_id":1,"message_id":mids()}],
      ["GroupCreate",{"msg_type":"GroupCreate","sender":0,"ids":gids(),"x1":0,"y1":2800,"x2":1000,"y2":3000,"name":"Site2",type:"site", "message_id":mids()}],
  ];

    var getMouseEventResult = function (mouseEvent) {
      return "(" + mouseEvent.screenX + ", " + mouseEvent.screenX + ")";
    };

    $scope.updateScaledXY = function() {
        $scope.scaledX = ($scope.mouseX - $scope.panX) / $scope.current_scale;
        $scope.scaledY = ($scope.mouseY - $scope.panY) / $scope.current_scale;
        $scope.view_port.x = - $scope.panX / $scope.current_scale;
        $scope.view_port.y = - $scope.panY / $scope.current_scale;
        $scope.view_port.width = $scope.graph.width / $scope.current_scale;
        $scope.view_port.height = $scope.graph.height / $scope.current_scale;
    };

    $scope.updatePanAndScale = function() {
        var g = document.getElementById('frame_g');
        g.setAttribute('transform','translate(' + $scope.panX + ',' + $scope.panY + ') scale(' + $scope.current_scale + ')');
    };

    $scope.clear_selections = function () {

        var i = 0;
        var j = 0;
        var devices = $scope.devices;
        var links = $scope.links;
        var groups = $scope.groups;
        $scope.selected_items = [];
        $scope.selected_devices = [];
        $scope.selected_links = [];
        $scope.selected_interfaces = [];
        $scope.selected_groups = [];
        for (i = 0; i < devices.length; i++) {
            for (j = 0; j < devices[i].interfaces.length; j++) {
                devices[i].interfaces[j].selected = false;
            }
            if (devices[i].selected) {
                $scope.send_control_message(new messages.DeviceUnSelected($scope.client_id, devices[i].id));
            }
            devices[i].selected = false;
        }
        for (i = 0; i < links.length; i++) {
            if (links[i].selected) {
                $scope.send_control_message(new messages.LinkUnSelected($scope.client_id, links[i].id));
            }
            links[i].selected = false;
        }
        for (i = 0; i < groups.length; i++) {
            groups[i].selected = false;
        }
    };

    $scope.select_items = function (multiple_selection) {

        var i = 0;
        var j = 0;
        var devices = $scope.devices;
        var last_selected_device = null;
        var last_selected_interface = null;
        var last_selected_link = null;

        $scope.pressedX = $scope.mouseX;
        $scope.pressedY = $scope.mouseY;
        $scope.pressedScaledX = $scope.scaledX;
        $scope.pressedScaledY = $scope.scaledY;

        if (!multiple_selection) {
            $scope.clear_selections();
        }

        for (i = devices.length - 1; i >= 0; i--) {
            if (devices[i].is_selected($scope.scaledX, $scope.scaledY)) {
                devices[i].selected = true;
                $scope.send_control_message(new messages.DeviceSelected($scope.client_id, devices[i].id));
                last_selected_device = devices[i];
				  if ($scope.selected_items.indexOf($scope.devices[i]) === -1) {
					  $scope.selected_items.push($scope.devices[i]);
				  }
                if ($scope.selected_devices.indexOf(devices[i]) === -1) {
                    $scope.selected_devices.push(devices[i]);
                }
                if (!multiple_selection) {
                    break;
                }
            }
        }

        // Do not select interfaces if a device was selected
        if (last_selected_device === null && !$scope.hide_interfaces) {
            for (i = devices.length - 1; i >= 0; i--) {
                for (j = devices[i].interfaces.length - 1; j >= 0; j--) {
                    if (devices[i].interfaces[j].is_selected($scope.scaledX, $scope.scaledY)) {
                        devices[i].interfaces[j].selected = true;
                        last_selected_interface = devices[i].interfaces[j];
                        if ($scope.selected_interfaces.indexOf($scope.devices[i].interfaces[j]) === -1) {
                            $scope.selected_interfaces.push($scope.devices[i].interfaces[j]);
                        }
                        if ($scope.selected_items.indexOf($scope.devices[i].interfaces[j]) === -1) {
                            $scope.selected_items.push($scope.devices[i].interfaces[j]);
                        }
                        if (!multiple_selection) {
                            break;
                        }
                    }
                }
            }
        }

        // Do not select links if a device was selected
        if (last_selected_device === null && last_selected_interface === null) {
            for (i = $scope.links.length - 1; i >= 0; i--) {
                if($scope.links[i].is_selected($scope.scaledX, $scope.scaledY)) {
                    $scope.links[i].selected = true;
                    $scope.send_control_message(new messages.LinkSelected($scope.client_id, $scope.links[i].id));
                    last_selected_link = $scope.links[i];
                    if ($scope.selected_items.indexOf($scope.links[i]) === -1) {
                        $scope.selected_items.push($scope.links[i]);
                    }
                    if ($scope.selected_links.indexOf($scope.links[i]) === -1) {
                        $scope.selected_links.push($scope.links[i]);
                        if (!multiple_selection) {
                            break;
                        }
                    }
                }
            }
        }

        return {last_selected_device: last_selected_device,
                last_selected_link: last_selected_link,
                last_selected_interface: last_selected_interface,
               };
    };

    // Event Handlers

    $scope.onMouseDown = function ($event) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseEvent($scope.client_id, $event.offsetX, $event.offsetY, $event.type));
      }
      $scope.last_event = $event;
      $scope.first_controller.handle_message('MouseDown', $event);
      $scope.onMouseDownResult = getMouseEventResult($event);
	  $event.preventDefault();
    };

    $scope.onMouseUp = function ($event) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseEvent($scope.client_id, $event.offsetX, $event.offsetY, $event.type));
      }
      $scope.last_event = $event;
      $scope.first_controller.handle_message('MouseUp', $event);
      $scope.onMouseUpResult = getMouseEventResult($event);
	  $event.preventDefault();
    };

    $scope.onMouseLeave = function ($event) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseEvent($scope.client_id, $event.offsetX, $event.offsetY, $event.type));
      }
      $scope.onMouseLeaveResult = getMouseEventResult($event);
      $scope.cursor.hidden = true;
	  $event.preventDefault();
    };

    $scope.onMouseMove = function ($event) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseEvent($scope.client_id, $event.offsetX, $event.offsetY, $event.type));
      }
      //var coords = getCrossBrowserElementCoords($event);
      $scope.cursor.hidden = false;
      $scope.cursor.x = $event.offsetX;
      $scope.cursor.y = $event.offsetY;
      $scope.mouseX = $event.offsetX;
      $scope.mouseY = $event.offsetY;
      $scope.updateScaledXY();
      $scope.first_controller.handle_message('MouseMove', $event);
      $scope.onMouseMoveResult = getMouseEventResult($event);
	  $event.preventDefault();
    };

    $scope.onMouseOver = function ($event) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseEvent($scope.client_id, $event.x, $event.offsetY, $event.type));
      }
      $scope.onMouseOverResult = getMouseEventResult($event);
      $scope.cursor.hidden = false;
	  $event.preventDefault();
    };

    $scope.onMouseEnter = $scope.onMouseOver;

    $scope.onMouseWheel = function ($event, delta, deltaX, deltaY) {
      if ($scope.recording) {
          $scope.send_control_message(new messages.MouseWheelEvent($scope.client_id, delta, deltaX, deltaY, $event.type, $event.originalEvent.metaKey));
      }
      $scope.last_event = $event;
      $scope.first_controller.handle_message('MouseWheel', [$event, delta, deltaX, deltaY]);
      event.preventDefault();
    };

    $scope.onKeyDown = function ($event) {
        if ($scope.recording) {
            $scope.send_control_message(new messages.KeyEvent($scope.client_id,
                                                              $event.key,
                                                              $event.keyCode,
                                                              $event.type,
                                                              $event.altKey,
                                                              $event.shiftKey,
                                                              $event.ctrlKey,
                                                              $event.metaKey));
        }
        $scope.last_event = $event;
        $scope.last_key = $event.key;
        $scope.last_key_code = $event.keyCode;
        $scope.first_controller.handle_message('KeyDown', $event);
        $scope.$apply();
        $event.preventDefault();
    };

    $document.bind("keydown", $scope.onKeyDown);

    // Touch Event Handlers
    //

	$scope.onTouchStart = function($event) {
     var touches = [];
     var i = 0;
     for (i = 0; i < $event.touches.length; i++) {
           touches.push({screenX: $event.touches[i].screenX, screenY: $event.touches[i].screenY});
     }
     $scope.touches = touches;
     if ($scope.recording) {
          $scope.send_control_message(new messages.TouchEvent($scope.client_id, "touchstart", touches));
     }

     if ($event.touches.length === 1) {
          $scope.cursor.hidden = false;
          $scope.cursor.x = $event.touches[0].screenX;
          $scope.cursor.y = $event.touches[0].screenY;
          $scope.mouseX = $event.touches[0].screenX;
          $scope.mouseY = $event.touches[0].screenY;
          $scope.updateScaledXY();
     }
      $scope.first_controller.handle_message('TouchStart', $event);
      $scope.onTouchStartEvent = $event;
	  $event.preventDefault();
	};

	$scope.onTouchEnd = function($event) {
     var touches = [];
     var i = 0;
     for (i = 0; i < $event.touches.length; i++) {
           touches.push({screenX: $event.touches[i].screenX, screenY: $event.touches[i].screenY});
     }
     $scope.touches = touches;
     if ($scope.recording) {
          $scope.send_control_message(new messages.TouchEvent($scope.client_id, "touchend", touches));
     }
      $scope.first_controller.handle_message('TouchEnd', $event);
      $scope.onTouchEndEvent = $event;
	  $event.preventDefault();
	};

	$scope.onTouchMove = function($event) {
     var touches = [];
     var i = 0;
     for (i = 0; i < $event.touches.length; i++) {
           touches.push({screenX: $event.touches[i].screenX, screenY: $event.touches[i].screenY});
     }
     $scope.touches = touches;
     if ($scope.recording) {
          $scope.send_control_message(new messages.TouchEvent($scope.client_id, "touchmove", touches));
     }

     if ($event.touches.length === 1) {
          $scope.cursor.hidden = false;
          $scope.cursor.x = $event.touches[0].screenX;
          $scope.cursor.y = $event.touches[0].screenY;
          $scope.mouseX = $event.touches[0].screenX;
          $scope.mouseY = $event.touches[0].screenY;
          $scope.updateScaledXY();
     }

      $scope.first_controller.handle_message('TouchMove', $event);
      $scope.onTouchMoveEvent = $event;
	  $event.preventDefault();
	};

    // Button Event Handlers
    //


    $scope.onDeployButton = function () {
        $scope.send_control_message(new messages.Deploy($scope.client_id));
    };

    $scope.onDestroyButton = function () {
        $scope.resetStatus();
        $scope.send_control_message(new messages.Destroy($scope.client_id));
    };

    $scope.onRecordButton = function () {
        $scope.recording = ! $scope.recording;
        if ($scope.recording) {
            $scope.send_control_message(new messages.MultipleMessage($scope.client_id,
                                                                     [new messages.StartRecording($scope.client_id),
                                                                      new messages.ViewPort($scope.client_id,
                                                                                            $scope.current_scale,
                                                                                            $scope.panX,
                                                                                            $scope.panY)]));
        } else {
            $scope.send_control_message(new messages.StopRecording($scope.client_id));
        }
    };

    $scope.onExportButton = function () {
        $scope.cursor.hidden = true;
        $scope.debug.hidden = true;
        $scope.hide_buttons = true;
        setTimeout(function () {
            svg_crowbar.svg_crowbar();
            $scope.cursor.hidden = false;
            $scope.hide_buttons = false;
            $scope.$apply();
        }, 1000);
    };

    $scope.onLayoutButton = function () {
        $scope.send_control_message(new messages.Layout($scope.client_id));
    };

    $scope.onDiscoverButton = function () {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "http://" + window.location.host + "/api/v1/job_templates/7/launch/", true);
        xhr.onload = function () {
            console.log(xhr.readyState);
        };
        xhr.onerror = function () {
            console.error(xhr.statusText);
        };
        xhr.send();
    };

    $scope.onConfigureButton = function () {
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "http://" + window.location.host + "/api/v1/job_templates/9/launch/", true);
        xhr.onload = function () {
            console.log(xhr.readyState);
        };
        xhr.onerror = function () {
            console.error(xhr.statusText);
        };
        xhr.send();
    };

    $scope.onTogglePhysical = function () {
        $scope.hide_links = false;
    };

    $scope.onUnTogglePhysical = function () {
        $scope.hide_links = true;
    };

    $scope.onToggleGroup = function () {
        $scope.hide_groups = false;
    };

    $scope.onUnToggleGroup = function () {
        $scope.hide_groups = true;
        $scope.group_controller.changeState(group.Ready);
    };

    // Buttons

    $scope.buttons = [
      new models.Button("BUTTON1", 10, 10, 90, 30, util.noop),
      new models.Button("BUTTON1", 110, 10, 90, 30, util.noop),
    ];

    var LAYERS_X = 160;

    $scope.layers = [
      new models.ToggleButton("TOGGLEBUTTON1", $scope.graph.width - LAYERS_X, 10, 150, 30, util.noop, util.noop, true),
      new models.ToggleButton("TOGGLEBUTTON2", $scope.graph.width - LAYERS_X, 50, 150, 30, util.noop, util.noop, true),
    ];

    var STENCIL_X = 10;
    var STENCIL_Y = 100;
    var STENCIL_SPACING = 40;

    $scope.stencils = [
      new models.Button("BUTTON3", STENCIL_X, STENCIL_Y + STENCIL_SPACING * 0, 90, 30, util.noop),
      new models.Button("BUTTON4", STENCIL_X, STENCIL_Y + STENCIL_SPACING * 1, 90, 30, util.noop),
    ];

    $scope.all_buttons = [];
    $scope.all_buttons.extend($scope.buttons);
    $scope.all_buttons.extend($scope.layers);
    $scope.all_buttons.extend($scope.stencils);

    $scope.onTaskStatus = function(data) {
        var i = 0;
        var j = 0;
        var found = false;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].name === data.device_name) {
                found = false;
                for (j = 0; j < $scope.devices[i].tasks.length; j++) {
                    if ($scope.devices[i].tasks[j].id === data.task_id) {
                        found = true;
                    }
                }
                if (!found) {
                    $scope.devices[i].tasks.push(new models.Task(data.task_id,
                                                                 data.device_name));
                }
                for (j = 0; j < $scope.devices[i].tasks.length; j++) {
                    if ($scope.devices[i].tasks[j].id === data.task_id) {
                        if (data.status !== null) {
                            $scope.devices[i].tasks[j].status = data.status === "pass";
                        }
                        if (data.working !== null) {
                            $scope.devices[i].tasks[j].working = data.working;
                        }
                    }
                }
            }
        }
    };

    $scope.onDeviceStatus = function(data) {
        var i = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].name === data.name) {
                if (data.status !== null) {
                    $scope.devices[i].status = data.status === "pass";
                }
                if (data.working !== null) {
                    $scope.devices[i].working = data.working;
                }
            }
        }
    };

    $scope.onFacts = function(data) {
        var i = 0;
        var j = 0;
        var k = 0;
        var device = null;
        var keys = null;
        var peers = null;
        var ptm = null;
        var intf = null;
        for (i = 0; i < $scope.devices.length; i++) {
            device = $scope.devices[i];
            if (device.name === data.key) {

                //Check PTM
                if (data.value.ansible_local !== undefined &&
                    data.value.ansible_local.ptm !== undefined) {
                    keys = Object.keys(data.value.ansible_local.ptm);
                    for (j = 0; j < keys.length; j++) {
                        ptm = data.value.ansible_local.ptm[keys[j]];
                        for (k = 0; k < device.interfaces.length; k++) {
                            intf = device.interfaces[k];
                            if (intf.name === ptm.port) {
                                intf.link.status = ptm['cbl status'] === 'pass';
                            }
                        }
                    }
                }

                //Check LLDP
                if (data.value.ansible_net_neighbors !== undefined) {
                    keys = Object.keys(data.value.ansible_net_neighbors);
                    for (j = 0; j < keys.length; j++) {
                        peers = data.value.ansible_net_neighbors[keys[j]];
                        for (k = 0; k < peers.length; k++) {
                            intf = $scope.getDeviceInterface(device.name, keys[j]);
                            if (intf !== null && intf.link !== null) {
                                if (intf.link.to_interface === intf) {
                                    intf.link.status = ($scope.getDeviceInterface(peers[k].host, peers[k].port) === intf.link.from_interface);
                                } else {
                                    intf.link.status = ($scope.getDeviceInterface(peers[k].host, peers[k].port) === intf.link.to_interface);
                                }
                            }
                        }
                    }
                }
            }
        }

        $scope.$apply();
    };

    $scope.getDevice = function(name) {

        var i = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].name === name) {
                return $scope.devices[i];
            }
        }

        return null;
    };

    $scope.getDeviceInterface = function(device_name, interface_name) {

        var i = 0;
        var k = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].name === device_name) {
                for (k = 0; k < $scope.devices[i].interfaces.length; k++) {
                    if ($scope.devices[i].interfaces[k].name === interface_name) {
                        return $scope.devices[i].interfaces[k];
                    }
                }
            }
        }
        return null;
    };

    $scope.onDeviceCreate = function(data) {
        $scope.create_device(data);
    };

    $scope.create_device = function(data) {
        var device = new models.Device(data.id,
                                       data.name,
                                       data.x,
                                       data.y,
                                       data.type);
        $scope.devices.push(device);
    };

    $scope.onGroupCreate = function(data) {
        $scope.create_group(data);
    };

    $scope.create_group = function(data) {
        var group = new models.Group(data.id,
                                     data.name,
                                     data.type,
                                     data.x1,
                                     data.y1,
                                     data.x2,
                                     data.y2,
                                     false);
        $scope.groups.push(group);
    };

    $scope.forDevice = function(device_id, data, fn) {
        var i = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === device_id) {
                fn($scope.devices[i], data);
                break;
            }
        }
    };

    $scope.forLink = function(link_id, data, fn) {
        var i = 0;
        for (i = 0; i < $scope.links.length; i++) {
            if ($scope.links[i].id === link_id) {
                fn($scope.links[i], data);
                break;
            }
        }
    };

    $scope.forDeviceInterface = function(device_id, interface_id, data, fn) {
        var i = 0;
        var j = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === device_id) {
                for (j = 0; j < $scope.devices[i].interfaces.length; j++) {
                    if ($scope.devices[i].interfaces[j].id === interface_id) {
                        fn($scope.devices[i].interfaces[j], data);
                        break;
                    }
                }
            }
        }
    };

    $scope.forGroup = function(group_id, data, fn) {
        var i = 0;
        for (i = 0; i < $scope.groups.length; i++) {
            if ($scope.groups[i].id === group_id) {
                fn($scope.groups[i], data);
                break;
            }
        }
    };

    $scope.onDeviceLabelEdit = function(data) {
        $scope.edit_device_label(data);
    };

    $scope.edit_device_label = function(data) {
        $scope.forDevice(data.id, data, function(device, data) {
            device.name = data.name;
        });
    };

    $scope.onInterfaceCreate = function(data) {
        $scope.create_interface(data);
    };

    $scope.create_interface = function(data) {
        var i = 0;
        var new_interface = new models.Interface(data.id, data.name);
        for (i = 0; i < $scope.devices.length; i++){
            if ($scope.devices[i].id === data.device_id) {
                $scope.devices[i].interface_seq = util.natural_numbers(data.id);
                new_interface.device = $scope.devices[i];
                $scope.devices[i].interfaces.push(new_interface);
            }
        }
    };

    $scope.onInterfaceLabelEdit = function(data) {
        $scope.edit_interface_label(data);
    };

    $scope.edit_interface_label = function(data) {
        $scope.forDeviceInterface(data.device_id, data.id, data, function(intf, data) {
            intf.name = data.name;
        });
    };

    $scope.onLinkCreate = function(data) {
        $scope.create_link(data);
    };

    $scope.create_link = function(data) {
        var i = 0;
        var j = 0;
        var new_link = new models.Link(null, null, null, null);
        new_link.id = data.id;
        $scope.link_id_seq = util.natural_numbers(data.id);
        for (i = 0; i < $scope.devices.length; i++){
            if ($scope.devices[i].id === data.from_device_id) {
                new_link.from_device = $scope.devices[i];
                for (j = 0; j < $scope.devices[i].interfaces.length; j++){
                    if ($scope.devices[i].interfaces[j].id === data.from_interface_id) {
                        new_link.from_interface = $scope.devices[i].interfaces[j];
                        $scope.devices[i].interfaces[j].link = new_link;
                    }
                }
            }
        }
        for (i = 0; i < $scope.devices.length; i++){
            if ($scope.devices[i].id === data.to_device_id) {
                new_link.to_device = $scope.devices[i];
                for (j = 0; j < $scope.devices[i].interfaces.length; j++){
                    if ($scope.devices[i].interfaces[j].id === data.to_interface_id) {
                        new_link.to_interface = $scope.devices[i].interfaces[j];
                        $scope.devices[i].interfaces[j].link = new_link;
                    }
                }
            }
        }
        if (new_link.from_interface !== null && new_link.to_interface !== null) {
            new_link.from_interface.dot();
            new_link.to_interface.dot();
        }
        if (new_link.from_device !== null && new_link.to_device !== null) {
            $scope.links.push(new_link);
        }
    };

    $scope.onLinkDestroy = function(data) {
        $scope.destroy_link(data);
    };

    $scope.destroy_link = function(data) {
        var i = 0;
        var link = null;
        var index = -1;
        for (i = 0; i < $scope.links.length; i++) {
            link = $scope.links[i];
            if (link.id === data.id &&
                link.from_device.id === data.from_device_id &&
                link.to_device.id === data.to_device_id &&
                link.to_interface.id === data.to_interface_id &&
                link.from_interface.id === data.from_interface_id) {
                link.from_interface.link = null;
                link.to_interface.link = null;
                index = $scope.links.indexOf(link);
                $scope.links.splice(index, 1);
            }
        }
    };

    $scope.onLinkLabelEdit = function(data) {
        $scope.edit_link_label(data);
    };

    $scope.edit_link_label = function(data) {
        $scope.forLink(data.id, data, function(link, data) {
            link.name = data.name;
        });
    };

    $scope.onDeviceMove = function(data) {
        $scope.move_device(data);
    };

    $scope.move_device = function(data) {
        var i = 0;
        var j = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === data.id) {
                $scope.devices[i].x = data.x;
                $scope.devices[i].y = data.y;
                for (j = 0; j < $scope.devices[i].interfaces.length; j ++) {
                    $scope.devices[i].interfaces[j].dot();
                    if ($scope.devices[i].interfaces[j].link !== null) {
                        $scope.devices[i].interfaces[j].link.to_interface.dot();
                        $scope.devices[i].interfaces[j].link.from_interface.dot();
                    }
                }
                break;
            }
        }
    };

    $scope.onDeviceDestroy = function(data) {
        $scope.destroy_device(data);
    };

    $scope.destroy_device = function(data) {

        // Delete the device and any links connecting to the device.
        var i = 0;
        var j = 0;
        var dindex = -1;
        var lindex = -1;
        var devices = $scope.devices.slice();
        var all_links = $scope.links.slice();
        for (i = 0; i < devices.length; i++) {
            if (devices[i].id === data.id) {
                dindex = $scope.devices.indexOf(devices[i]);
                if (dindex !== -1) {
                    $scope.devices.splice(dindex, 1);
                }
                lindex = -1;
                for (j = 0; j < all_links.length; j++) {
                    if (all_links[j].to_device === devices[i] ||
                        all_links[j].from_device === devices[i]) {
                        lindex = $scope.links.indexOf(all_links[j]);
                        if (lindex !== -1) {
                            $scope.links.splice(lindex, 1);
                        }
                    }
                }
            }
        }
    };


    $scope.onGroupLabelEdit = function(data) {
        $scope.edit_group_label(data);
    };

    $scope.edit_group_label = function(data) {
        $scope.forGroup(data.id, data, function(group, data) {
            group.name = data.name;
        });
    };

    $scope.redo = function(type_data) {
        var type = type_data[0];
        var data = type_data[1];

        if (type === "DeviceMove") {
            $scope.move_device(data);
        }

        if (type === "DeviceCreate") {
            $scope.create_device(data);
        }

        if (type === "DeviceDestroy") {
            $scope.destroy_device(data);
        }

        if (type === "DeviceLabelEdit") {
            $scope.edit_device_label(data);
        }

        if (type === "LinkCreate") {
            $scope.create_link(data);
        }

        if (type === "LinkDestroy") {
            $scope.destroy_link(data);
        }
    };


    $scope.undo = function(type_data) {
        var type = type_data[0];
        var data = type_data[1];
        var inverted_data;

        if (type === "DeviceMove") {
            inverted_data = angular.copy(data);
            inverted_data.x = data.previous_x;
            inverted_data.y = data.previous_y;
            $scope.move_device(inverted_data);
        }

        if (type === "DeviceCreate") {
            $scope.destroy_device(data);
        }

        if (type === "DeviceDestroy") {
            inverted_data = new messages.DeviceCreate(data.sender,
                                                      data.id,
                                                      data.previous_x,
                                                      data.previous_y,
                                                      data.previous_name,
                                                      data.previous_type);
            $scope.create_device(inverted_data);
        }

        if (type === "DeviceLabelEdit") {
            inverted_data = angular.copy(data);
            inverted_data.name = data.previous_name;
            $scope.edit_device_label(inverted_data);
        }

        if (type === "LinkCreate") {
            $scope.destroy_link(data);
        }

        if (type === "LinkDestroy") {
            $scope.create_link(data);
        }
    };

    $scope.onClientId = function(data) {
        $scope.client_id = data;
    };

    $scope.onTopology = function(data) {
        $scope.topology_id = data.topology_id;
        $scope.panX = data.panX;
        $scope.panY = data.panX;
        $scope.current_scale = data.scale;
        $scope.link_id_seq = util.natural_numbers(data.link_id_seq);
        $scope.group_id_seq = util.natural_numbers(data.group_id_seq);
        $scope.device_id_seq = util.natural_numbers(data.device_id_seq);
        $location.search({topology_id: data.topology_id});
    };

    $scope.onDeviceSelected = function(data) {
        var i = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === data.id) {
                $scope.devices[i].remote_selected = true;
            }
        }
    };

    $scope.onDeviceUnSelected = function(data) {
        var i = 0;
        for (i = 0; i < $scope.devices.length; i++) {
            if ($scope.devices[i].id === data.id) {
                $scope.devices[i].remote_selected = false;
            }
        }
    };

    $scope.onHistory = function (data) {

        $scope.history = [];
        var i = 0;
        for (i = 0; i < data.length; i++) {
            $scope.history.push(data[i]);
        }
    };

    $scope.onSnapshot = function (data) {

        //Erase the existing state
        $scope.devices = [];
        $scope.links = [];

        var device_map = {};
        var device_interface_map = {};
        var i = 0;
        var j = 0;
        var device = null;
        var intf = null;
        var new_device = null;
        var new_intf = null;
        var max_device_id = null;
        var max_link_id = null;
        var max_group_id = null;
        var min_x = null;
        var min_y = null;
        var max_x = null;
        var max_y = null;
        var new_link = null;
        var new_group = null;

        //Build the devices
        for (i = 0; i < data.devices.length; i++) {
            device = data.devices[i];
            if (max_device_id === null || device.id > max_device_id) {
                max_device_id = device.id;
            }
            if (min_x === null || device.x < min_x) {
                min_x = device.x;
            }
            if (min_y === null || device.y < min_y) {
                min_y = device.y;
            }
            if (max_x === null || device.x > max_x) {
                max_x = device.x;
            }
            if (max_y === null || device.y > max_y) {
                max_y = device.y;
            }
            new_device = new models.Device(device.id,
                                           device.name,
                                           device.x,
                                           device.y,
                                           device.type);
            new_device.interface_seq = util.natural_numbers(device.interface_id_seq);
            $scope.devices.push(new_device);
            device_map[device.id] = new_device;
            device_interface_map[device.id] = {};
            for (j = 0; j < device.interfaces.length; j++) {
                intf = device.interfaces[j];
                new_intf = (new models.Interface(intf.id,
                                                 intf.name));
				new_intf.device = new_device;
                device_interface_map[device.id][intf.id] = new_intf;
                new_device.interfaces.push(new_intf);
            }
        }

        //Build the links
        var link = null;
        for (i = 0; i < data.links.length; i++) {
            link = data.links[i];
            if (max_link_id === null || link.id > max_link_id) {
                max_link_id = link.id;
            }
            new_link = new models.Link(link.id,
                                       device_map[link.from_device_id],
                                       device_map[link.to_device_id],
                                       device_interface_map[link.from_device_id][link.from_interface_id],
                                       device_interface_map[link.to_device_id][link.to_interface_id]);
            new_link.name = link.name;
            $scope.links.push(new_link);
            device_interface_map[link.from_device_id][link.from_interface_id].link = new_link;
            device_interface_map[link.to_device_id][link.to_interface_id].link = new_link;
        }

        //Build the groups
        var group = null;
        for (i = 0; i < data.groups.length; i++) {
            group = data.groups[i];
            if (max_group_id === null || group.id > max_group_id) {
                max_group_id = group.id;
            }
            new_group = new models.Group(group.id,
                                         group.name,
                                         group.type,
                                         group.x1,
                                         group.y1,
                                         group.x2,
                                         group.y2,
                                         false);
            if (group.members !== undefined) {
                for (j=0; j < group.members.length; j++) {
                    new_group.devices.push(device_map[group.members[j]]);
                }
            }
            $scope.groups.push(new_group);
        }

        var diff_x;
        var diff_y;

        // Calculate the new scale to show the entire diagram
        if (min_x !== null && min_y !== null && max_x !== null && max_y !== null) {
            diff_x = max_x - min_x;
            diff_y = max_y - min_y;

            $scope.current_scale = Math.min(2, Math.max(0.10, Math.min((window.innerWidth-200)/diff_x, (window.innerHeight-300)/diff_y)));
            $scope.updateScaledXY();
            $scope.updatePanAndScale();
        }
        // Calculate the new panX and panY to show the entire diagram
        if (min_x !== null && min_y !== null) {
            diff_x = max_x - min_x;
            diff_y = max_y - min_y;
            $scope.panX = $scope.current_scale * (-min_x - diff_x/2) + window.innerWidth/2;
            $scope.panY = $scope.current_scale * (-min_y - diff_y/2) + window.innerHeight/2;
            $scope.updateScaledXY();
            $scope.updatePanAndScale();
        }

        //Update the device_id_seq to be greater than all device ids to prevent duplicate ids.
        if (max_device_id !== null) {
            $scope.device_id_seq = util.natural_numbers(max_device_id);
        }
        //
        //Update the link_id_seq to be greater than all link ids to prevent duplicate ids.
        if (max_link_id !== null) {
            $scope.link_id_seq = util.natural_numbers(max_link_id);
        }
        //Update the group_id_seq to be greater than all group ids to prevent duplicate ids.
        if (max_group_id !== null) {
            $scope.group_id_seq = util.natural_numbers(max_group_id);
        }

        $scope.updateInterfaceDots();
    };

    $scope.updateInterfaceDots = function() {
        var i = 0;
        var j = 0;
        var devices = $scope.devices;
        for (i = devices.length - 1; i >= 0; i--) {
            for (j = devices[i].interfaces.length - 1; j >= 0; j--) {
                devices[i].interfaces[j].dot();
            }
        }
    };

    $scope.resetStatus = function() {
        var i = 0;
        var j = 0;
        var devices = $scope.devices;
        var links = $scope.links;
        for (i = 0; i < devices.length; i++) {
            devices[i].status = null;
            devices[i].working = false;
            devices[i].tasks = [];
            for (j = devices[i].interfaces.length - 1; j >= 0; j--) {
                devices[i].interfaces[j].status = null;
            }
        }
        for (i = 0; i < links.length; i++) {
            links[i].status = null;
        }
    };

    $scope.send_coverage = function () {
        if (typeof(window.__coverage__) !== "undefined" && window.__coverage__ !== null) {
            $scope.send_control_message(new messages.Coverage($scope.client_id, window.__coverage__));
        }
    };


    $scope.control_socket.onmessage = function(message) {
        $scope.first_controller.handle_message('Message', message);
        $scope.$apply();
    };

	$scope.control_socket.onopen = function() {
        //Ignore
	};

	// Call onopen directly if $scope.control_socket is already open
	if ($scope.control_socket.readyState === WebSocket.OPEN) {
		$scope.control_socket.onopen();
	}

    $scope.send_control_message = function (message) {
        var i = 0;
        message.sender = $scope.client_id;
        message.message_id = $scope.message_id_seq();
        if (message.constructor.name === "MultipleMessage") {
            for (i=0; i < message.messages.length; i++) {
                message.messages[i].message_id = $scope.message_id_seq();
            }
        }
        //var data = messages.serialize(message);
        //console.log(data);
    };


    // End web socket
    //

	angular.element($window).bind('resize', function(){

		$scope.graph.width = $window.innerWidth;
	  	$scope.graph.right_column = $window.innerWidth - 300;
	  	$scope.graph.height = $window.innerHeight;

        $scope.update_size();

		// manuall $digest required as resize event
		// is outside of angular
	 	$scope.$digest();
    });

    //60fps ~ 17ms delay
    setInterval( function () {
        $scope.frame = Math.floor(window.performance.now());
        $scope.$apply();
    }, 17);

    console.log("Network Widgets started");

    $scope.$on('$destroy', function () {
        console.log("Network Widgets stopping");
        $document.unbind('keydown', $scope.onKeyDown);
    });

    $scope.update_size = function () {
        var i = 0;
        for (i = 0; i < $scope.layers.length; i++) {
            $scope.layers[i].x = $scope.graph.width - 140;
        }
    };

    for (i =0; i < $scope.initial_messages.length; i++) {
        console.log(['Inital message',  $scope.initial_messages[i]]);
        $scope.first_controller.handle_message($scope.initial_messages[i][0], $scope.initial_messages[i][1]);
    }

    $scope.updateScaledXY();
    $scope.updatePanAndScale();

    for (i=0; i < $scope.groups.length; i++) {
        $scope.groups[i].update_membership($scope.devices, $scope.groups);
    }

    $scope.update_offsets = function () {

        var i = 0;
        var streams = $scope.streams;
        var map = new Map();
        var stream = null;
        var key = null;
        for (i = 0; i < streams.length; i++) {
            stream = streams[i];
            key = "" + stream.from_device.id + "_" + stream.to_device.id;
            map.set(key, 0);
        }
        for (i = 0; i < streams.length; i++) {
            stream = streams[i];
            key = "" + stream.from_device.id + "_" + stream.to_device.id;
            stream.offset = map.get(key);
            map.set(key, stream.offset + 1);
        }
    };
};

exports.NetworkWidgetsController = NetworkWidgetsController;
console.log("Network Widgets loaded");
