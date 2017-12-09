

Building
========

To build the UI:

make

To push the UI to AWX code base:

make deploy



Getting Started With Development
================================


**Introduction**

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
trigonometry, and analytic geometry are useful when working with this code.

* See: <https://en.wikipedia.org/wiki/Analytic_geometry>

**Design choices**

Certain design choices were made to make the UI performant and scale to a large
number of nodes in a diagram.  These include the use of simple ES5 functions for
better performance over more advanced functions.  For instance C-style for-loops
were many times faster than implementations of forEach or iterators which make
function calls during each iteration.  This basic ES5 style should be followed
throughout the implementation of the Network UI.

**AngularJS**

The Networking UI component uses AngularJS 1.6.x for part of the rendering pipeline
but it is not a normal AngularJS web application.  AngularJS makes use of
data-binding and watchers which I found do not scale to the number of elements
we are trying to support in the Networking UI.   The Networking UI only uses
AngularJS for SVG rendering (using AngularJS templates) which does scale
sufficiently.


**AngularJS Controllers**

Instead of creating many AngularJS controllers and directives the networking UI
uses one big controller to hold the state of the entire UI.  Normally this is
an anti-pattern in AngularJS.  Here is was necessary to scale to a large number
of on-screen elements.

**AngularJS Directives**

* See: <https://docs.angularjs.org/guide/directive>

AngularJS directives are used in the networking UI application using the element
matching style and the templateUrl option to include a template. A majority of
the directives are defined in `src/network.ui.app.js`.

* See: `src/network.ui.app.js`
```
    .directive('awxNetDeviceDetail', deviceDetail.deviceDetail)
```

* See: `src/device.detail.directive.js`
```
function deviceDetail () {
  return { restrict: 'A', templateUrl: '/static/network_ui/widgets/device_detail.html' };
}
```

**AngularJS Templates**

* See: <https://docs.angularjs.org/guide/templates>

Normal AngularJS templates are used with the networking UI controller.  
The templates can be foundin `/widgets`. Child
scopes are created for sub-templates using the `ng-repeat` directive.

In this example the `awx-net-link` directive expects a Link model to be
passed to it.  The Link model is defined in the `src/models.js` file.

* See: `src/link.directive.js`
* See: `widgets/link.html`

* See: `widgets/network_ui.html`:
```
    <g ng-repeat="link in links">
    <g awx-net-link></g>
    </g>
```

* See: `src/models.js`
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
 
The following example sets the toolbox.selected_item value to the variable 
item which the directives used in the child scope expect to be set.

* See: `widgets/inventory_toolbox.html`
```
<g ng-repeat="item in [toolbox.selected_item]">
```


**DOM (Document Object Model)**

No state is stored in or attached to the DOM.  All state is stored in
javascript objects attached to the network ui controller.

Direct DOM manipulation should not be used in the network UI unless absolutely
necessary. JQuery should not be used.  The DOM is generated through the use of
AngularJS templates.

**SVG (Scalable Vector Graphics)**

* See: <https://developer.mozilla.org/en-US/docs/Web/SVG>

The network UI is built as one large SVG element (the SVG canvas) with other
graphical elements (lines, circles, rectangles, paths, and text) absolutely
positioned within the outer most SVG element.  The browser is not involved with
layout of the elements within the SVG.   Each "widget" in the network UI needs
to track or calculate its own position on the SVG canvas. The z-level of the
elements are determined by the draw order on the canvas which is defined
in `widgets/network_ui.html`.  Elements drawn first will be hidden behind
elements drawn later.



**Rendering Pipeline**

Event -> Javscript objects -> AngularJS templates -> SVG

AngularJS is used to render the SVG inside the SVG canvas using directives
and templates.  AngularJS is also used to schedule when the SVG canvas will
be updated. When an input event comes from the user, or an event is received
over the websocket, javascript objects will be updated according the the network
UI code.  Then AngularJS will be notified that it needs to update the templates
either automatically for some events or explicitly using `$scope.$apply();` if
not handled automatically by AngularJS.  The templates will render to SVG and be
included in the DOM for the rest of the AWX UI.

Because the networking UI does not use watchers nor data-binding features of
AngularJS events flow in one way from event to javascript to angular to SVG.
Events do not flow backwards through this pipeline.

Clicking on an SVG element will not send the event to that SVG element directly
from the browser.   It must be routed through the network UI code first.


** SVG Primer **

SVG uses tags to define graphical elements just like HTML uses tags to define
text documents.   Commonly use tags include g, circle, rect, path, and text.
SVG elements are absolutely positioned within an SVG canvas.  The group tag, g,
is similar to the div tag in HTML.  Text in SVG must be contained in the text
tag and cannot be outside tags as in HTML.

* See: <https://developer.mozilla.org/en-US/docs/Web/SVG/Element>

Each tag that describes a visual element requires X and Y coordinates as input
to position that element. These coordinates are relative to position of the SVG
canvas. The network UI uses the entire page height and width for the SVG canvas
so that the position on the SVG on the canvas is the same as the position on
the page.


SVG supports graphical transformations on several tags to allow relative
positioning of sub-elements which makes calculating the X and Y positions
easier.   The network UI uses transformations often for this purpose.
Transformations that are often used here are the translate, scale, and rotate
transforms.  Translate moves the origin of the coordinate system to a new point
for the sub-elements.  Scale multiplies the size of the units in a coordinate
system by some factor.  Rotate performs a rotation about the origin by some
number of degrees.  These functions are converted to a matrix operation on the
coordinate system which can be efficiently applied.  It is often useful to use
the transforms to simplify the calculations of X and Y coordinates instead of
calculating those values in javascript. Also these transforms make developing
widgets much easier since we only need to keep up with a single point for the
widget and all other points can be relatively positioned from that point.
Hard-coding positions in widget development is the normal case since transforms
can change the size and position of the widget when the widget is applied to
the canvas.  Only when necessary should we calculate positions of parts of a
widget in javascript.

* See: <https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform>


SVG paths are a mini-language for defining graphics operations in one tag. It
is often used to create shapes that are more complex than lines, rectangles,
and circles.  It is very useful for defining arcs.

* See: <https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths>

**SVG and CSS**

CSS and SVG work really nicely together for setting style, colors, and fonts in SVG.
The SVG uses different attributes for setting colors than does HTML elements.
Most SVG elements use `stroke` and `fill` to define the colors and `stroke-width`
to define the width of lines and curves. The attributes `font-family` and `font-size`
are used to set the font for text elements in SVG.  The network UI uses the Less
CSS compiler and BEM naming conventions to simplify and organize CSS.

* See: src/style.less
* See: <http://lesscss.org/>
* See: <http://getbem.com/introduction/>

**Events**

All mouse and keyboard events are captured by the outer most element of the
network UI.  Mouse movements, mouse clicks, and key presses are all routed by
the network UI code and not by the browser.  This is done to implement
interactions with the virtual graphical canvas that are not supported by the
browser.  "Simple" things like buttons and text fields have to be handled by
the network UI code instead of relying on the browser to route the mouse click
to the appropriate object.


The following code captures all the mouse movements, mouse clicks, mouse wheel,
and touch events and sends them to the corresponding network UI controller functions.

* See: widgets/network_ui.html

```
    <svg id="frame" class="NetworkUI"
         ng-attr-height="{{graph.height}}"
         ng-attr-width="{{graph.width}}"
         ng-mousedown="onMouseDown($event)"
         ng-mouseup="onMouseUp($event)"
         ng-mouseenter="onMouseEnter($event)"
         ng-mouseleave="onMouseLeave($event)"
         ng-mousemove="onMouseMove($event)"
         ng-mouseover="onMouseOver($event)"
         ng-touchstart="onTouchStart($event)"
         ng-touchmove="onTouchMove($event)"
         ng-touchend="onTouchEnd($event)"
         ng-tap="onTap($event)"
         msd-wheel="onMouseWheel($event, $delta, $deltaX, $deltaY)">
```


Key events are captured by the following code:

* See: src/network.ui.controller.js

```
    $document.bind("keydown", $scope.onKeyDown);
```

**Describing Behavior with Finite State Machines**

To implement complex UI interactions predictably and correctly is a tough
problem.  Often the problem is solved by creating a large library of generic
reusable components that are rigorously tested and hardened by a large group of
developers over a period of several years. Eventually the myriad bugs are
hammered out at great expense.  Only then can the UI components be reliably
used.  This code does not follow that approach.

The workflows this code supports require very specific UI components that are
not found in generic libraries.  The interactions we want to support are not
available in generic libraries.  This code develops from scratch only the
components that are necessary to implement the workflows of designing and
operating networks of devices.

This code defines those elements using finite state machines to process the
events from user input and other software components.  Programming with finite
state machines allows us to define formally complex behavior that would
normally be informally defined by branches, functions, object interactions, and
object inheritance.  Formal definition eliminates much of the unexpected
behavior that causes defects in the software.

* See: <https://en.wikipedia.org/wiki/Finite-state_machine>

Finite state machines can be represented as a directed graph of labeled nodes and labeled edges
which can be both be represented visually and in machine readable code.

The network UI uses finite state machines to describe what happens when the software receives
an input.   

