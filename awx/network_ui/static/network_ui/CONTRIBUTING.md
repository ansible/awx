

Building
========

To build the UI:

make

To push the UI to AWX code base:

make deploy



Getting Started With Development
================================


Introduction:

The Networking UI component of AWX works differently from the rest of the AWX
web UI to support high-scale interactive graphical design of networking
topologies.

The Networking UI is a virtual graphical canvas where graphical elements are
drawn upon.  This canvas supports panning (scrolling horizontally and
vertically) and scaling (zooming in and out), dynamic changing of modes, and
other features that would be very difficult or impossible to implement with
standard HTML events and rendering.

This interface is more like computer graphics than it is building a styled text
document with interactive components.  A good grasp of cartesian coordinates,
trignometry, and analytic geometry are useful when working with this code.

See: <https://en.wikipedia.org/wiki/Analytic_geometry>

Design choices:

Certain design choices were made to make the UI performant and scale to a large
number of nodes in a diagram.  These include the use of simple ES5 forms for
better performance over more advanced forms.  For instance C-style for-loops
were many times faster than implementations of forEach or iterators which make
function calls during each iteration.  This basic ES5 style should be followed
throughout the implementation of the Network UI.

AngularJS:

The Networking UI component uses AngularJS 1.6.x for part of the rendering pipeline
but it is not a normal AngularJS web application.  AngularJS makes use of
data-binding and watchers which I found do not scale to the number of elements
we are trying to support in the Networking UI.   The Networking UI only uses
AngularJS for SVG rendering (using AnguarJS templates) which does scale
sufficiently.


AngularJS Controllers:

Instead of creating many AngularJS controllers and directives the networking UI
uses one big controller to hold the state of the entire UI.  Normally this is
an anti-pattern in AngularJS.  Here is was necessary to scale to a large number
of on-screen elements.

AngularJS Directives:

See: <https://docs.angularjs.org/guide/directive>

AngularJS directives are used in the networking UI application using the element
matching style and the templateUrl option to include a template.

See: src/network.ui.app.js
```
    .directive('awxNetDeviceDetail', deviceDetail.deviceDetail)
```

See: src/device.detail.directive.js
```
function deviceDetail () {
  return { restrict: 'A', templateUrl: '/static/network_ui/widgets/device_detail.html' };
}
```

AngularJS Templates:

See: <https://docs.angularjs.org/guide/templates>

Normal AngularJS templates are used with the networking UI controller.  Child
scopes are created for subtemplates using the `ng-repeat` directive.

In this example the awx-net-link directive expects a Link model to be
passed to it.  The Link model is defined in the src/models.js file.

See: widgets/network_ui.html
See: widgets/link.html

See: src/link.directive.js
```
    <g ng-repeat="link in links">
    <g awx-net-link></g>
    </g> <!-- end ng-repeat link in links-->
```

See: src/models.js
```
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
```

In some cases we need to set a variable in a child scope to a value.  In the
scheme language this is called `let`. AngularJS is missing a ng-let directive
but this can be simulated with ng-repeat and a list. The following example
sets the toolbox.selected_item value to the variable item which the directives
used in the child scope expect to be set.

See: <https://docs.racket-lang.org/reference/let.html> (Optional reference, just look if you are curious)

See: widgets/inventory_toolbox.html
```
<g ng-repeat="item in [toolbox.selected_item]">
```


DOM:

No state is stored in or attached to the DOM.  All state is stored in
javascript objects attached to the network ui controller.

Direct DOM manipulation should not be used in the network UI unless absolutely
necessary. JQuery should not be used.  The DOM is generated through the use of
AngularJS templates.

SVG (Scalable Vector Graphics):

See: <https://developer.mozilla.org/en-US/docs/Web/SVG>

The network UI is built as one large SVG element (the SVG canvas) with other
graphical elements (lines, circles, rectangles, paths, and text) absolutely
placed within the outer most SVG element.  The browser is not involved with
layout of the elements within the SVG.   Each "widget" in the network UI needs
to track or calculate its own position on the SVG canvas. The z-level of the
elements are determined by the draw order on the canvas which is defined
in `widgets/network_ui.html`.  Elements drawn first will be hidden behind
elements drawn later.

Rendering Pipeline:

Event -> Javscript objects -> AngularJS templates -> SVG

AngularJS is used to render the SVG inside the SVG canvas using directives
and templates.  AngularJS is also used to schedule when the SVG canvas will
be updated. When an input event comes from the user or an event is received
over the websocket javascript objects will be updated according the the network
UI code.  Then AngularJS will be notified that it needs to update the templates
either automatically for some events or explicitly using `$scope.$apply();` if
not handled automatically by AngularJS.  The templates will render to SVG and be
included in the DOM for the rest of the AWX UI.

Because the networking UI does not use watchers nor data-binding features of
AngularJS events flow in one way from event to javascript to angular to SVG.
Events do not flow backwards through this pipeline.

Clicking on an SVG element will not send the event to that SVG element directly
from the browser.   It must be routed through the network UI code first.

Events:

All mouse and keyboard events are captured by the outer most element of the
network UI.  Mouse movements, mouse clicks, and key presses are all routed by
the network UI code and not by the browser.  This is done to implement
interactions with the virtual graphical canvas that are not supported by the
browser.  "Simple" things like buttons and text fields have to be handled by
the network UI code instead of relying on the browser to route the mouse click
to the appropriate object.
