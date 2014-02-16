'use strict';


var fs   = require('fs');
var path = require('path');
var util = require('util');
var yaml = require('../lib/js-yaml');


// Let define a couple of classes...

function Point(x, y, z) {
  this.klass = 'Point';
  this.x     = x;
  this.y     = y;
  this.z     = z;
}


function Space(height, width, points) {
  if (points) {
    if (!points.every(function (point) { return point instanceof Point; })) {
      throw new Error('A non-Point inside a points array!');
    }
  }

  this.klass  = 'Space';
  this.height = height;
  this.width  = width;
  this.points = points;
}


// Let's define YAML types to load and dump our Point/Space objects.

var pointYamlType = new yaml.Type('!point', {
  //
  // The information used to load a Point.
  //
  loadKind: 'sequence', // See node kinds in YAML spec: http://www.yaml.org/spec/1.2/spec.html#kind//
  loadResolver: function (state) {
    // You can access actual data from YAML via `state.result`.
    // After the resolving, you should put the resolved value into `state.result`.

    if (3 === state.result.length) { // `state.result`
      state.result = new Point(state.result[0], state.result[1], state.result[2]);
      return true; // Resolved successfully.
    } else {
      return false; // Can't resolve.
    }
  },
  //
  // The information used to dump a Point.
  //
  dumpInstanceOf: Point, // Dump only instances of Point constructor as this YAML type.
  dumpRepresenter: function (point) {
    // Represent in YAML as three-element sequence.
    return [ point.x, point.y, point.z ];
  }
});


var spaceYamlType = new yaml.Type('!space', {
  loadKind: 'mapping',
  loadResolver: function (state) {
    state.result = new Space(state.result.height, state.result.width, state.result.points);
    return true;
  },
  dumpInstanceOf: Space
  // `dumpRepresenter` is omitted here. So, Space objects will be dumped as is.
  // That is regular mapping with three key-value pairs but with !space tag.
});


// After our types are defined, it's time to join them into a schema.

var SPACE_SCHEMA = yaml.Schema.create([ spaceYamlType, pointYamlType ]);


// And read a document using that schema.

fs.readFile(path.join(__dirname, 'custom_types.yaml'), 'utf8', function (error, data) {
  var loaded;

  if (!error) {
    loaded = yaml.load(data, { schema: SPACE_SCHEMA });
    console.log(util.inspect(loaded, false, 20, true));
  } else {
    console.error(error.stack || error.message || String(error));
  }
});


// There are some exports to play with this example interactively.

module.exports.Point         = Point;
module.exports.Space         = Space;
module.exports.pointYamlType = pointYamlType;
module.exports.spaceYamlType = spaceYamlType;
module.exports.SPACE_SCHEMA  = SPACE_SCHEMA;
