

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
trignometry, and analytic geometry is useful when working with this code.

See: <https://en.wikipedia.org/wiki/Analytic_geometry>

Design choices:

Certain design choices were made to make the UI performant and scale to a large
number of nodes in a diagram.  These include the use of simple ES5 forms for
better performance over more advanced forms.  For instance C-style for-loops
were many times faster than implementations of forEach or iterators which make
function calls during each iteration.  These basic ES5 style should be followed
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

See: <https://docs.racket-lang.org/reference/let.html>

See: widgets/inventory_toolbox.html
```
<g ng-repeat="item in [toolbox.selected_item]">
```


Events:

All mouse and keyboard events are captured by the outer most element of the
network UI.

Rendering Pipeline:

Javscript objects -> AngularJS templates -> SVG


