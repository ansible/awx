/* Copyright (c) 2017 Red Hat, Inc. */
var angular = require('angular');
var fsm = require('./fsm.js');
var mode_fsm = require('./mode.fsm.js');
var hotkeys = require('./hotkeys.fsm.js');
var toolbox_fsm = require('./toolbox.fsm.js');
var view = require('./view.fsm.js');
var move = require('./move.fsm.js');
var buttons = require('./buttons.fsm.js');
var time = require('./time.fsm.js');
var test_fsm = require('./test.fsm.js');
var util = require('./util.js');
var models = require('./models.js');
var messages = require('./messages.js');
var animations = require('./animations.js');
var keybindings = require('./keybindings.fsm.js');
var details_panel_fsm = require('./details.panel.fsm.js');
var svg_crowbar = require('./vendor/svg-crowbar.js');
var ReconnectingWebSocket = require('reconnectingwebsocket');

var NetworkUIController = function($scope,
                                   $document,
                                   $location,
                                   $window,
                                   $http,
                                   $q,
                                   $state,
                                   ProcessErrors,
                                   ConfigService,
                                   rbacUiControlService) {

  window.scope = $scope;

  $scope.http = $http;

  $scope.api_token = '';
  $scope.disconnected = false;

  $scope.topology_id = 0;
  // Create a web socket to connect to the backend server

  $scope.inventory_id = $state.params.inventory_id;

  var protocol = null;

  if ($location.protocol() === 'http') {
    protocol = 'ws';
  } else if ($location.protocol() === 'https') {
    protocol = 'wss';
  }

  $scope.initial_messages = [];
  if (!$scope.disconnected) {
      $scope.control_socket = new ReconnectingWebSocket(protocol + "://" + window.location.host + "/network_ui/topology?inventory_id=" + $scope.inventory_id,
                                                         null,
                                                         {debug: false, reconnectInterval: 300});
      $scope.test_socket = new ReconnectingWebSocket(protocol + "://" + window.location.host + "/network_ui/test?inventory_id=" + $scope.inventory_id,
                                                         null,
                                                         {debug: false, reconnectInterval: 300});
  } else {
      $scope.control_socket = {
          on_message: util.noop
      };
  }
  $scope.my_location = $location.protocol() + "://" + $location.host() + ':' + $location.port();
  $scope.client_id = 0;
  $scope.test_client_id = 0;
  $scope.onMouseDownResult = "";
  $scope.onMouseUpResult = "";
  $scope.onMouseEnterResult = "";
  $scope.onMouseLeaveResult = "";
  $scope.onMouseMoveResult = "";
  $scope.onMouseMoveResult = "";
  $scope.current_scale = 1.0;
  $scope.current_mode = null;
  $scope.panX = 0;
  $scope.panY = 0;
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
  $scope.new_link = null;
  $scope.new_stream = null;
  $scope.last_key = "";
  $scope.last_key_code = null;
  $scope.last_event = null;
  $scope.cursor = {'x':100, 'y': 100, 'hidden': true};

  $scope.debug = {'hidden': true};
  $scope.hide_buttons = false;
  $scope.hide_menus = false;
  $scope.hide_links = false;
  $scope.hide_interfaces = false;
  $scope.graph = {'width': window.innerWidth,
                  'right_column': 300,
                  'height': window.innerHeight};
  $scope.MAX_ZOOM = 5;
  $scope.MIN_ZOOM = 0.1;
  $scope.device_id_seq = util.natural_numbers(0);
  $scope.link_id_seq = util.natural_numbers(0);
  $scope.message_id_seq = util.natural_numbers(0);
  $scope.test_result_id_seq = util.natural_numbers(0);
  $scope.animation_id_seq = util.natural_numbers(0);
  $scope.overall_toolbox_collapsed = false;
  $scope.time_pointer = -1;
  $scope.frame = 0;
  $scope.recording = false;
  $scope.replay = false;
  $scope.devices = [];
  $scope.devices_by_name = {};
  $scope.links = [];
  $scope.links_in_vars_by_device = {};
  $scope.tests = [];
  $scope.current_tests = [];
  $scope.current_test = null;
  $scope.template_building = false;
  $scope.version = null;
  $scope.test_events = [];
  $scope.test_results = [];
  $scope.test_errors = [];
  $scope.animations = [];
  $scope.sequences = {};
  $scope.view_port = {'x': 0,
                      'y': 0,
                      'width': 0,
                      'height': 0,
                  };
  $scope.trace_id_seq = util.natural_numbers(0);
  $scope.trace_order_seq = util.natural_numbers(0);
  $scope.trace_id = $scope.trace_id_seq();
  $scope.jump = {from_x: 0,
                 from_y: 0,
                 to_x: 0,
                 to_y: 0};

    $scope.send_trace_message = function (message) {
        if (!$scope.recording) {
            return;
        }
        message.sender = $scope.test_client_id;
        message.trace_id = $scope.trace_id;
        message.message_id = $scope.message_id_seq();
        var data = messages.serialize(message);
        if (!$scope.disconnected) {
            try {
                $scope.test_socket.send(data);
            }
            catch(err) {
                $scope.initial_messages.push(message);
            }
        }
    };

    $scope.onKeyDown = function ($event) {
        if ($scope.recording) {
            $scope.send_test_message(new messages.KeyEvent($scope.test_client_id,
                                                           $event.key,
                                                           $event.keyCode,
                                                           $event.type,
                                                           $event.altKey,
                                                           $event.shiftKey,
                                                           $event.ctrlKey,
                                                           $event.metaKey,
                                                           $scope.trace_id));
        }
        $scope.last_event = $event;
        $scope.last_key = $event.key;
        $scope.last_key_code = $event.keyCode;
        $scope.first_channel.send('KeyDown', $event);
        $scope.$apply();
        $event.preventDefault();
    };

  //Define the FSMs
  $scope.hotkeys_controller = new fsm.FSMController($scope, "hotkeys_fsm", hotkeys.Start, $scope);
  $scope.keybindings_controller = new fsm.FSMController($scope, "keybindings_fsm", keybindings.Start, $scope);
  $scope.view_controller = new fsm.FSMController($scope, "view_fsm", view.Start, $scope);
  $scope.move_controller = new fsm.FSMController($scope, "move_fsm", move.Start, $scope);
  $scope.details_panel_controller = new fsm.FSMController($scope, "details_panel_fsm", details_panel_fsm.Start, $scope);
  $scope.buttons_controller = new fsm.FSMController($scope, "buttons_fsm", buttons.Start, $scope);
  $scope.time_controller = new fsm.FSMController($scope, "time_fsm", time.Start, $scope);
  $scope.test_controller = new fsm.FSMController($scope, "test_fsm", test_fsm.Start, $scope);

  $scope.inventory_toolbox_controller = new fsm.FSMController($scope, "toolbox_fsm", toolbox_fsm.Start, $scope);

  var toolboxTopMargin = $('.Networking-top').height();
  var toolboxTitleMargin = toolboxTopMargin + 35;
  var toolboxHeight = $scope.graph.height - $('.Networking-top').height();

  $scope.update_links_in_vars_by_device = function (device_name, variables) {

      var j = 0;
      var link = null;

       if (variables.ansible_topology !== undefined) {
           if (variables.ansible_topology.links !== undefined) {
               for (j=0; j < variables.ansible_topology.links.length; j++) {
                   link = variables.ansible_topology.links[j];
                   if (link.remote_device_name !== undefined &&
                       link.remote_interface_name !== undefined &&
                       link.name !== undefined) {
                        if ($scope.links_in_vars_by_device[device_name] === undefined) {
                            $scope.links_in_vars_by_device[device_name] = [];
                        }
                        if ($scope.links_in_vars_by_device[link.remote_device_name] === undefined) {
                            $scope.links_in_vars_by_device[link.remote_device_name] = [];
                        }
                        $scope.links_in_vars_by_device[device_name].push({
                            from_interface: link.name,
                            to_interface: link.remote_interface_name,
                            from_device: device_name,
                            to_device: link.remote_device_name
                        });
                        $scope.links_in_vars_by_device[link.remote_device_name].push({
                            from_interface: link.remote_interface_name,
                            to_interface: link.name,
                            from_device: link.remote_device_name,
                            to_device: device_name
                        });
                   }
               }
           }
       }
  };

  //Inventory Toolbox Setup
  $scope.inventory_toolbox = new models.ToolBox(0, 'Inventory', 'device', 0, toolboxTopMargin, 200, toolboxHeight);
  if (!$scope.disconnected) {
      $http.get('/api/v2/inventories/' + $scope.inventory_id + '/hosts/')
           .then(function(response) {
               var devices_by_name = {};
               var i = 0;
               for (i = 0; i < $scope.devices.length; i++) {
                   devices_by_name[$scope.devices[i].name] = $scope.devices[i];
               }
               let hosts = response.data.results;
               console.log(hosts.length);
               for(i = 0; i<hosts.length; i++) {
                   console.log(i);
                   try {
                       let device_type = null;
                       let device_name = null;
                       let device = null;
                       let host = hosts[i];
                       device_name = host.name;
                       console.log(device_name);
                       if (host.variables !== "") {
                           host.data = jsyaml.safeLoad(host.variables);
                           console.log(host.data);
                       } else {
                           host.data = {};
                       }
                       if (host.data.ansible_topology === undefined) {
                           device_type = 'unknown';
                       } else {
                           if (host.data.ansible_topology.type === undefined) {
                               device_type = 'unknown';
                           } else {
                               device_type = host.data.ansible_topology.type;
                           }

                           $scope.update_links_in_vars_by_device(device_name, host.data);
                       }
                       if (devices_by_name[device_name] === undefined) {
                           console.log(['adding', device_name]);
                           device = new models.Device(0, device_name, 0, 0, device_type, host.id);
                           device.icon = true;
                           device.variables = host.data;
                           $scope.inventory_toolbox.items.push(device);
                       }
                   } catch (error) {
                       console.log(error);
                   }
               }
           })
           .catch(({data, status}) => {
               ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get host data: ' + status });
           });
  }
  $scope.inventory_toolbox.spacing = 150;
  $scope.inventory_toolbox.enabled = true;
  $scope.inventory_toolbox.title_coordinates = {x: 60, y: toolboxTitleMargin};
  $scope.inventory_toolbox_controller.toolbox = $scope.inventory_toolbox;
  $scope.inventory_toolbox_controller.remove_on_drop = true;
  $scope.inventory_toolbox_controller.debug = true;
  $scope.inventory_toolbox_controller.dropped_action = function (selected_item) {
    $scope.first_channel.send("PasteDevice", new messages.PasteDevice(selected_item));
  };

  //End Inventory Toolbox Setup

  $scope.mode_controller = new fsm.FSMController($scope, "mode_fsm", mode_fsm.Start, $scope);

  //Wire up the FSMs
  $scope.keybindings_controller.delegate_channel = new fsm.Channel($scope.keybindings_controller,
                                                            $scope.hotkeys_controller,
                                                            $scope);

  $scope.view_controller.delegate_channel = new fsm.Channel($scope.view_controller,
                                                            $scope.keybindings_controller,
                                                            $scope);
  $scope.move_controller.delegate_channel = new fsm.Channel($scope.move_controller,
                                                            $scope.view_controller,
                                                            $scope);
  $scope.details_panel_controller.delegate_channel = new fsm.Channel($scope.details_panel_controller,
                                                            $scope.move_controller,
                                                            $scope);
  $scope.inventory_toolbox_controller.delegate_channel = new fsm.Channel($scope.inventory_toolbox_controller,
                                                            $scope.details_panel_controller,
                                                            $scope);
  $scope.buttons_controller.delegate_channel = new fsm.Channel($scope.buttons_controller,
                                                            $scope.inventory_toolbox_controller,
                                                            $scope);
  $scope.time_controller.delegate_channel = new fsm.Channel($scope.time_controller,
                                                            $scope.buttons_controller,
                                                            $scope);
  $scope.mode_controller.delegate_channel = new fsm.Channel($scope.mode_controller,
                                                            $scope.time_controller,
                                                            $scope);
  $scope.test_controller.delegate_channel = new fsm.Channel($scope.test_controller,
                                                            $scope.mode_controller,
                                                            $scope);


  $scope.first_channel = new fsm.Channel(null,
                                         $scope.mode_controller,
                                         $scope);

  $scope.test_channel = new fsm.Channel(null,
                                        $scope.test_controller,
                                        $scope);

    var getMouseEventResult = function (mouseEvent) {
      return "(" + mouseEvent.x + ", " + mouseEvent.y + ")";
    };

    $scope.updateScaledXY = function() {
        if (isNaN($scope.mouseX) ||
            isNaN($scope.mouseY) ||
            isNaN($scope.panX) ||
            isNaN($scope.panY) ||
            isNaN($scope.current_scale)) {
            return;
        }
        $scope.scaledX = ($scope.mouseX - $scope.panX) / $scope.current_scale;
        $scope.scaledY = ($scope.mouseY - $scope.panY) / $scope.current_scale;
        $scope.view_port.x = - $scope.panX / $scope.current_scale;
        $scope.view_port.y = - $scope.panY / $scope.current_scale;
        $scope.view_port.width = $scope.graph.width / $scope.current_scale;
        $scope.view_port.height = $scope.graph.height / $scope.current_scale;

    };

    $scope.updatePanAndScale = function() {
        if (isNaN($scope.panX) ||
            isNaN($scope.panY) ||
            isNaN($scope.current_scale)) {
            return;
        }
        var g = document.getElementById('frame_g');
        g.setAttribute('transform','translate(' + $scope.panX + ',' + $scope.panY + ') scale(' + $scope.current_scale + ')');
    };

    $scope.to_virtual_coordinates = function (b_x, b_y) {
        var v_x = (b_x - $scope.panX) / $scope.current_scale;
        var v_y = (b_y - $scope.panY) / $scope.current_scale;
        return {x: v_x, y: v_y};
    };

    $scope.to_pan = function (v_x, v_y) {
        var p_x = v_x * $scope.current_scale * -1;
        var p_y = v_y * $scope.current_scale * -1;
        return {x: p_x, y: p_y};
    };

    $scope.clear_selections = function () {

        var i = 0;
	    var j = 0;
        var devices = $scope.devices;
        var links = $scope.links;
        $scope.selected_items = [];
        $scope.selected_devices = [];
        $scope.selected_links = [];
        $scope.selected_interfaces = [];
        for (i = 0; i < links.length; i++) {
            if (links[i].selected) {
                $scope.send_control_message(new messages.LinkUnSelected($scope.client_id, links[i].id));
            }
            links[i].selected = false;
        }
        for (i = 0; i < devices.length; i++) {
            for (j = 0; j < devices[i].interfaces.length; j++) {
                devices[i].interfaces[j].selected = false;
            }
            if (devices[i].selected) {
                $scope.send_control_message(new messages.DeviceUnSelected($scope.client_id, devices[i].id));
            }
            devices[i].selected = false;
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
                if ($scope.links[i].is_selected($scope.scaledX, $scope.scaledY)) {
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

    $scope.normalize_mouse_event = function ($event) {
        if ($event.pageX !== undefined) {
            $event.x = $event.pageX;
        }
        if ($event.pageY !== undefined) {
            $event.y = $event.pageY;
        }
        if ($event.originalEvent !== undefined) {
            var originalEvent = $event.originalEvent;
            if (originalEvent.wheelDelta !== undefined) {
                $event.delta = $event.originalEvent.wheelDelta;
            }
            if (originalEvent.wheelDeltaX !== undefined) {
                $event.deltaX = $event.originalEvent.wheelDeltaX;
            }
            if (originalEvent.wheelDeltaY !== undefined) {
                $event.deltaY = $event.originalEvent.wheelDeltaY;
            }
        }
    };

    $scope.onMouseDown = function ($event) {
      $scope.normalize_mouse_event($event);
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseEvent($scope.test_client_id, $event.x, $event.y, $event.type, $scope.trace_id));
      }
      $scope.last_event = $event;
      $scope.first_channel.send('MouseDown', $event);
      $scope.onMouseDownResult = getMouseEventResult($event);
      $event.preventDefault();
    };

    $scope.onMouseUp = function ($event) {
      $scope.normalize_mouse_event($event);
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseEvent($scope.test_client_id, $event.x, $event.y, $event.type, $scope.trace_id));
      }
      $scope.last_event = $event;
      $scope.first_channel.send('MouseUp', $event);
      $scope.onMouseUpResult = getMouseEventResult($event);
      $event.preventDefault();
    };

    $scope.onMouseLeave = function ($event) {
      $scope.normalize_mouse_event($event);
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseEvent($scope.test_client_id, $event.x, $event.y, $event.type, $scope.trace_id));
      }
      $scope.onMouseLeaveResult = getMouseEventResult($event);
      $event.preventDefault();
    };

    $scope.onMouseMove = function ($event) {
      $scope.normalize_mouse_event($event);
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseEvent($scope.test_client_id, $event.x, $event.y, $event.type, $scope.trace_id));
      }
      //var coords = getCrossBrowserElementCoords($event);
      $scope.cursor.x = $event.x;
      $scope.cursor.y = $event.y;
      $scope.mouseX = $event.x;
      $scope.mouseY = $event.y;
      $scope.updateScaledXY();
      $scope.first_channel.send('MouseMove', $event);
      $scope.onMouseMoveResult = getMouseEventResult($event);
      $event.preventDefault();
    };

    $scope.onMouseOver = function ($event) {
      $scope.normalize_mouse_event($event);
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseEvent($scope.test_client_id, $event.x, $event.y, $event.type, $scope.trace_id));
      }
      $scope.onMouseOverResult = getMouseEventResult($event);
      $event.preventDefault();
    };

    $scope.onMouseEnter = $scope.onMouseOver;

    $scope.onMouseWheel = function ($event) {
      $scope.normalize_mouse_event($event);
      var delta = $event.delta;
      var deltaX = $event.deltaX;
      var deltaY = $event.deltaY;
      if ($scope.recording) {
          $scope.send_test_message(new messages.MouseWheelEvent($scope.test_client_id, delta, deltaX, deltaY, $event.type, $event.originalEvent.metaKey, $scope.trace_id));
      }
      $scope.last_event = $event;
      $scope.first_channel.send('MouseWheel', [$event, delta, deltaX, deltaY]);
      $event.preventDefault();
    };

    // Conext Menu Button Handlers
    $scope.removeContextMenu = function(){
        $scope.move_controller.handle_message("Ready", {});
        let context_menu = $scope.context_menus[0];
        context_menu.enabled = false;
        context_menu.x = -100000;
        context_menu.y = -100000;
        context_menu.buttons.forEach(function(button){
            button.enabled = false;
            button.x = -100000;
            button.y = -100000;
        });
    };

    $scope.closeDetailsPanel = function () {
        $scope.first_channel.send('DetailsPanelClose', {});
    };

    $scope.onDetailsContextButton = function () {
        function emitCallback(item, canAdd){
            $scope.first_channel.send('DetailsPanel', {});
            $scope.removeContextMenu();
            $scope.update_toolbox_heights();
            $scope.$emit('awxNet-showDetails', item, canAdd);
        }

        // show details for devices
        if ($scope.selected_devices.length === 1 && $scope.selected_devices[0].host_id === 0){
            // following block is intended for devices added in the network UI but not in Tower
            emitCallback($scope.selected_devices[0]);
        }

        // following block is intended for devices that are saved in the API
        if ($scope.selected_devices.length === 1 && $scope.selected_devices[0].host_id !== 0){
            let host_id = $scope.selected_devices[0].host_id;
            let url = `/api/v2/hosts/${host_id}/`;
            let hostData = $http.get(url)
                 .then(function(response) {
                     let host = response.data;
                     host.host_id = host.id;
                     return host;
                 })
                 .catch(({data, status}) => {
                     ProcessErrors($scope, data, status, null, { hdr: 'Error!', msg: 'Failed to get host data: ' + status });
                 });
            let canAdd = rbacUiControlService.canAdd('hosts')
                    .then(function(res) {
                        return res.canAdd;
                    })
                    .catch(function() {
                        return false;
                    });
            Promise.all([hostData, canAdd]).then((values) => {
                let item = values[0];
                let canAdd = values[1];
                emitCallback(item, canAdd);
            });
        }

        // show details for interfaces
        else if($scope.selected_interfaces.length === 1){
            emitCallback($scope.selected_interfaces[0]);
        }

        // show details for links
        else if($scope.selected_links.length === 1){
            emitCallback($scope.selected_links[0]);
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

    $scope.deleteDevice = function(){
        var i = 0;
        var j = 0;
        var index = -1;
        var devices = $scope.selected_devices;
        var all_links = $scope.links.slice();
        $scope.selected_devices = [];
        $scope.selected_links = [];
        $scope.move_controller.changeState(move.Ready);
        for (i = 0; i < devices.length; i++) {
            index = $scope.devices.indexOf(devices[i]);
            if (index !== -1) {
                $scope.devices.splice(index, 1);
                $scope.devices_by_name[devices[i].name] = undefined;
                $scope.$emit('awxNet-removeSearchOption', devices[i]);
                devices[i].x = 0;
                devices[i].y = 0;
                devices[i].selected = false;
                devices[i].remote_selected = false;
                devices[i].interfaces = [];
                devices[i].interfaces_by_name = [];
                $scope.inventory_toolbox.items.push(devices[i]);
                $scope.send_control_message(new messages.DeviceDestroy($scope.client_id,
                                                                       devices[i].id,
                                                                       devices[i].x,
                                                                       devices[i].y,
                                                                       devices[i].name,
                                                                       devices[i].type,
                                                                       devices[i].host_id));
            }
            for (j = 0; j < all_links.length; j++) {
                if (all_links[j].to_device === devices[i] ||
                    all_links[j].from_device === devices[i]) {
                    index = $scope.links.indexOf(all_links[j]);
                    if (index !== -1) {
                        $scope.links.splice(index, 1);
                        $scope.send_control_message(new messages.LinkDestroy($scope.client_id,
                                                                             all_links[j].id,
                                                                             all_links[j].from_device.id,
                                                                             all_links[j].to_device.id,
                                                                             all_links[j].from_interface.id,
                                                                             all_links[j].to_interface.id,
                                                                             all_links[j].name));

                    }
                }
            }
        }
    };

    $scope.onDeleteContextMenu = function(){
        $scope.removeContextMenu();
        if($scope.selected_devices.length === 1){
            $scope.deleteDevice();
        }
    };

    $scope.$on('awxNet-hideToolbox', () => {
        $scope.first_channel.send("ToggleToolbox", {});
        $scope.overall_toolbox_collapsed = !$scope.overall_toolbox_collapsed;
    });

    $scope.$on('awxNet-toolbarButtonEvent', function(e, functionName){
        $scope[`on${functionName}Button`]();
    });

    $scope.$on('awxNet-SearchDropdown', function(){
        $scope.first_channel.send('SearchDropdown', {});
    });

    $scope.$on('awxNet-SearchDropdownClose', function(){
        $scope.first_channel.send('SearchDropdownClose', {});
    });

    $scope.$on('awxNet-search', function(e, device){

        var searched;
        for(var i = 0; i < $scope.devices.length; i++){
            if(Number(device.id) === $scope.devices[i].id){
                searched = $scope.devices[i];
            }
        }
        searched.selected = true;
        $scope.selected_devices.push(searched);
        $scope.jump_to_animation(searched.x, searched.y, 1.0);
    });

    $scope.jump_to_animation = function(jump_to_x, jump_to_y, jump_to_scale, updateZoom) {
        $scope.cancel_animations();
        var v_center = $scope.to_virtual_coordinates($scope.graph.width/2, $scope.graph.height/2);
        $scope.jump.from_x = v_center.x;
        $scope.jump.from_y = v_center.y;
        $scope.jump.to_x = jump_to_x;
        $scope.jump.to_y = jump_to_y;
        var distance = util.distance(v_center.x, v_center.y, jump_to_x, jump_to_y);
        var num_frames = 30 * Math.floor((1 + 4 * distance / (distance + 3000)));
        var scale_animation = new models.Animation($scope.animation_id_seq(),
                                                  num_frames,
                                                  {
                                                      c: -0.1,
                                                      distance: distance,
                                                      end_height: (1.0/jump_to_scale) - 1,
                                                      current_scale: $scope.current_scale,
                                                      scope: $scope,
                                                      updateZoomBoolean: updateZoom
                                                  },
                                                  $scope,
                                                  $scope,
                                                  animations.scale_animation);
        $scope.animations.push(scale_animation);
        var pan_animation = new models.Animation($scope.animation_id_seq(),
                                                  num_frames,
                                                  {
                                                      x2: jump_to_x,
                                                      y2: jump_to_y,
                                                      x1: v_center.x,
                                                      y1: v_center.y,
                                                      scope: $scope
                                                  },
                                                  $scope,
                                                  $scope,
                                                  animations.pan_animation);
        $scope.animations.push(pan_animation);
    };

    $scope.$on('awxNet-zoom', (e, zoomPercent) => {
        let v_center = $scope.to_virtual_coordinates($scope.graph.width/2, $scope.graph.height/2);
        let scale = Math.pow(10, (zoomPercent - 120) / 40);
        $scope.jump_to_animation(v_center.x, v_center.y, scale, false);
    });

    $scope.onRecordButton = function () {
        $scope.recording = ! $scope.recording;
        if ($scope.recording) {
            $scope.trace_id = $scope.trace_id_seq();
            $scope.send_test_message(new messages.MultipleMessage($scope.test_client_id,
                                                                  [new messages.StartRecording($scope.test_client_id, $scope.trace_id),
                                                                   new messages.ViewPort($scope.test_client_id,
                                                                                         $scope.current_scale,
                                                                                         $scope.panX,
                                                                                         $scope.panY,
                                                                                         $scope.graph.width,
                                                                                         $scope.graph.height,
                                                                                         $scope.trace_id),
                                                                   new messages.Snapshot($scope.test_client_id,
                                                                                         $scope.devices,
                                                                                         $scope.links,
                                                                                         $scope.inventory_toolbox.items,
                                                                                         0,
                                                                                         $scope.trace_id)]));
        } else {
            $scope.send_test_message(new messages.MultipleMessage($scope.test_client_id,
                                                                  [new messages.Snapshot($scope.test_client_id,
                                                                                         $scope.devices,
                                                                                         $scope.links,
                                                                                         $scope.inventory_toolbox.items,
                                                                                         1,
                                                                                         $scope.trace_id),
                                                                   new messages.StopRecording($scope.test_client_id, $scope.trace_id)]));
        }
    };

    $scope.onExportButton = function () {
        $scope.cursor.hidden = true;
        $scope.debug.hidden = true;
        $scope.hide_buttons = true;
        $scope.hide_menus = true;
        setTimeout(function () {
            svg_crowbar.svg_crowbar();
            $scope.cursor.hidden = false;
            $scope.hide_buttons = false;
            $scope.hide_menus = false;
            $scope.$apply();
        }, 1000);
    };

    $scope.onExportYamlButton = function () {
        $window.open('/network_ui/topology.yaml?topology_id=' + $scope.topology_id , '_blank');
    };

    // Context Menu Buttons
    $scope.context_menu_buttons = [
        new models.ContextMenuButton("Details", 236, 231, 160, 26, $scope.onDetailsContextButton, $scope),
        new models.ContextMenuButton("Delete", 256, 231, 160, 26, $scope.onDeleteContextMenu, $scope)
    ];

    // Context Menus
    $scope.context_menus = [
        new models.ContextMenu('HOST', 210, 200, 160, 64, $scope.contextMenuCallback, false, $scope.context_menu_buttons, $scope)
    ];

    $scope.onDownloadTraceButton = function () {
        window.open("/network_ui_test/download_trace?topology_id=" + $scope.topology_id + "&trace_id=" + $scope.trace_id + "&client_id=" + $scope.test_client_id);
    };

    $scope.onDownloadRecordingButton = function () {
        window.open("/network_ui_test/download_recording?topology_id=" + $scope.topology_id + "&trace_id=" + $scope.trace_id + "&client_id=" + $scope.test_client_id);
    };

    $scope.onUploadTestButton = function () {
        window.open("/network_ui_test/upload_test", "_top");
    };

    $scope.onRunTestsButton = function () {

        $scope.test_results = [];
        $scope.current_tests = $scope.tests.slice();
        $scope.test_channel.send("EnableTest", new messages.EnableTest());
    };

    $scope.all_buttons = [];
    $scope.all_buttons.extend($scope.context_menu_buttons);

    $scope.onDeviceCreate = function(data) {
        $scope.create_device(data);
    };

    $scope.create_device = function(data) {
        console.log(data);
        var device = new models.Device(data.id,
                                       data.name,
                                       data.x,
                                       data.y,
                                       data.type,
                                       data.host_id);
        $scope.device_id_seq = util.natural_numbers(data.id);
        $scope.devices.push(device);
        $scope.devices_by_name[device.name] = device;
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

    $scope.onLinkCreate = function(data) {
        console.log(data);
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
        console.log(new_link);
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

    $scope.onClientId = function(data) {
        $scope.client_id = data;
    };

    $scope.onTopology = function(data) {
        $scope.topology_id = data.topology_id;
        $scope.panX = data.panX;
        $scope.panY = data.panX;
        $scope.current_scale = data.scale;
        $scope.$emit('awxNet-UpdateZoomWidget', $scope.current_scale, true);
        $scope.link_id_seq = util.natural_numbers(data.link_id_seq);
        $scope.device_id_seq = util.natural_numbers(data.device_id_seq);
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

    $scope.onSnapshot = function (data) {

        //Erase the existing state
        $scope.devices = [];
        $scope.links = [];
        $scope.devices_by_name = {};

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
        var min_x = null;
        var min_y = null;
        var max_x = null;
        var max_y = null;
        var new_link = null;

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
            if (device.device_type === undefined) {
                device.device_type = device.type;
            }
            new_device = new models.Device(device.id,
                                           device.name,
                                           device.x,
                                           device.y,
                                           device.device_type,
                                           device.host_id);
            if (device.variables !== undefined) {
                new_device.variables = device.variables;
            }

            for (j=0; j < $scope.inventory_toolbox.items.length; j++) {
                 if($scope.inventory_toolbox.items[j].name === device.name) {
                     $scope.inventory_toolbox.items.splice(j, 1);
                     break;
                 }
            }
            new_device.interface_seq = util.natural_numbers(device.interface_id_seq);
            new_device.process_id_seq = util.natural_numbers(device.process_id_seq);
            $scope.devices.push(new_device);
            $scope.devices_by_name[new_device.name] = new_device;
            device_map[device.id] = new_device;
            device_interface_map[device.id] = {};
            for (j = 0; j < device.interfaces.length; j++) {
                intf = device.interfaces[j];
                new_intf = (new models.Interface(intf.id,
                                                 intf.name));
                new_intf.device = new_device;
                device_interface_map[device.id][intf.id] = new_intf;
                new_device.interfaces.push(new_intf);
                new_device.interfaces_by_name[new_intf.name] = new_intf;
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

        var diff_x;
        var diff_y;

        // Calculate the new scale to show the entire diagram
        if (min_x !== null && min_y !== null && max_x !== null && max_y !== null) {
            diff_x = max_x - min_x;
            diff_y = max_y - min_y;

            $scope.current_scale = Math.min(2, Math.max(0.10, Math.min((window.innerWidth-200)/diff_x, (window.innerHeight-300)/diff_y)));
            $scope.$emit('awxNet-UpdateZoomWidget', $scope.current_scale, true);
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

        console.log(['data.inventory_toolbox', data.inventory_toolbox]);
        if (data.inventory_toolbox !== undefined) {
            $scope.inventory_toolbox.items = [];
            for (i = 0; i < data.inventory_toolbox.length; i++) {
                device = data.inventory_toolbox[i];
                console.log(device);
                if (device.device_type === undefined) {
                    device.device_type = device.type;
                }
                new_device = new models.Device(device.id,
                                               device.name,
                                               device.x,
                                               device.y,
                                               device.device_type,
                                               device.host_id);
				if (device.variables !== undefined) {
					new_device.variables = device.variables;
				}
                $scope.inventory_toolbox.items.push(new_device);
            }
            console.log($scope.inventory_toolbox.items);
        }

        $scope.updateInterfaceDots();
        $scope.$emit('awxNet-instatiateSelect', $scope.devices);
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

    $scope.control_socket.onmessage = function(message) {
        $scope.first_channel.send('Message', message);
        $scope.$apply();
    };

    $scope.control_socket.onopen = function() {
        //ignore
    };

    $scope.test_socket.onmessage = function(message) {
        $scope.test_channel.send('Message', message);
        $scope.$apply();
    };

    $scope.test_socket.onopen = function() {
        //ignore
    };

    // Call onopen directly if $scope.control_socket is already open
    if ($scope.control_socket.readyState === WebSocket.OPEN) {
        $scope.control_socket.onopen();
    }
    // Call onopen directly if $scope.test_socket is already open
    if ($scope.test_socket.readyState === WebSocket.OPEN) {
        $scope.test_socket.onopen();
    }

    $scope.send_test_message = function (message) {
        var i = 0;
        message.sender = $scope.test_client_id;
        message.message_id = $scope.message_id_seq();
        if (message.constructor.name === "MultipleMessage") {
            for (i=0; i < message.messages.length; i++) {
                message.messages[i].message_id = $scope.message_id_seq();
            }
        }
        var data = messages.serialize(message);
        if (!$scope.disconnected) {
            $scope.test_socket.send(data);
        }
    };

    $scope.send_control_message = function (message) {
        var i = 0;
        message.sender = $scope.client_id;
        message.message_id = $scope.message_id_seq();
        if (message.constructor.name === "MultipleMessage") {
            for (i=0; i < message.messages.length; i++) {
                message.messages[i].message_id = $scope.message_id_seq();
            }
        }
        var data = messages.serialize(message);
        if (!$scope.disconnected) {
            $scope.control_socket.send(data);
        }
    };


    // End web socket
    //

    angular.element($window).bind('resize', function(){

        $scope.graph.width = $window.innerWidth;
        $scope.graph.right_column = 300;
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

    console.log("Network UI started");

    $scope.$on('$destroy', function () {
        console.log("Network UI stopping");
        $scope.first_channel.send('UnbindDocument', {});
    });

    $scope.update_toolbox_heights = function(){
        var toolboxTopMargin = $('.Networking-top').height();
        var toolboxTitleMargin = toolboxTopMargin + 35;
        var toolboxHeight = $scope.graph.height - toolboxTopMargin;

        let toolboxes = ['inventory_toolbox'];
        toolboxes.forEach((toolbox) => {
            $scope[toolbox].y = toolboxTopMargin;
            $scope[toolbox].height = toolboxHeight;
            $scope[toolbox].title_coordinates.y = toolboxTitleMargin;
        });

        $('.Networking-detailPanel').height(toolboxHeight);
        $('.Networking-detailPanel').css('top', toolboxTopMargin);
    };

    $scope.update_size = function () {
        $scope.update_toolbox_heights();
    };

    setInterval( function () {
        var test_event = null;
        if ($scope.test_events.length  > 0) {
            test_event = $scope.test_events.shift();
            test_event.sender = 0;
            try {
                $scope.first_channel.send(test_event.msg_type, test_event);
            } catch (err) {
                console.log(["Test Error:", $scope.current_test, err]);
                $scope.test_errors.push(err);
            }
        }
        $scope.$apply();
    }, 10);

    ConfigService
        .getConfig()
        .then(function(config){
            $scope.version = config.version;
        });

    $scope.reset_coverage = function() {
        var i = null;
        var coverage = null;
        var f = null;
        if (typeof(window.__coverage__) !== "undefined" && window.__coverage__ !== null) {
            for (f in window.__coverage__) {
                coverage = window.__coverage__[f];
                for (i in coverage.b) {
                    coverage.b[i] = [0, 0];
                }
                for (i in coverage.f) {
                    coverage.f[i] = 0;
                }
                for (i in coverage.s) {
                    coverage.s[i] = 0;
                }
            }
        }
    };

    $scope.reset_flags = function () {
      $scope.debug = {'hidden': true};
      $scope.hide_buttons = false;
      $scope.hide_links = false;
      $scope.hide_interfaces = false;
    };


    $scope.reset_fsm_state = function () {
        $scope.hotkeys_controller.state = hotkeys.Start;
        $scope.hotkeys_controller.state.start($scope.hotkeys_controller);
        $scope.keybindings_controller.state = keybindings.Start;
        $scope.keybindings_controller.state.start($scope.keybindings_controller);
        $scope.view_controller.state = view.Start;
        $scope.view_controller.state.start($scope.view_controller);
        $scope.move_controller.state = move.Start;
        $scope.move_controller.state.start($scope.move_controller);
        $scope.details_panel_controller.state = details_panel_fsm.Start;
        $scope.details_panel_controller.state.start($scope.details_panel_controller);
        $scope.time_controller.state = time.Start;
        $scope.time_controller.state.start($scope.time_controller);
        $scope.inventory_toolbox_controller.state = toolbox_fsm.Start;
        $scope.inventory_toolbox_controller.state.start($scope.inventory_toolbox_controller);
        $scope.mode_controller.state = mode_fsm.Start;
        $scope.mode_controller.state.start($scope.mode_controller);
    };

    $scope.reset_toolboxes = function () {
        $scope.inventory_toolbox.items = [];
        $scope.inventory_toolbox.scroll_offset = 0;
    };

    $scope.cancel_animations = function () {

        var i = 0;
        for (i = 0; i < $scope.animations.length; i++) {
            this.animations[i].fsm.handle_message('AnimationCancelled');
        }
        $scope.animations = [];
    };
};

exports.NetworkUIController = NetworkUIController;
console.log("Network UI loaded");
