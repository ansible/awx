/* Copyright (c) 2017 Red Hat, Inc. */
Array.prototype.extend = function (other_array) {
    /* you should include a test to check whether other_array really is an array */
    var i = 0;
    for (i = 0; i < other_array.length; i++) {
        this.push(other_array[i]);
    }
};

var math = require('mathjs');
var yaml = require('js-yaml');
var nunjucks = require('nunjucks');

function nunjucks_find_variables (text) {

    var variables = [];
    var tokenizer = nunjucks.lexer.lex(text, {});
    var token = tokenizer.nextToken();
    while (token !== null) {
        if (token.type === 'variable-start') {
            token = tokenizer.nextToken();
            while (token !== null) {
                if (token.type === 'symbol') {
                    variables.push(token.value);
                }
                if (token.type === 'variable-end') {
                    break;
                }
                token = tokenizer.nextToken();
            }
        }
        token = tokenizer.nextToken();
    }

    return variables;
};
exports.nunjucks_find_variables = nunjucks_find_variables;

function parse_variables (variables) {
    var parsed_variables = {};
    try {
        parsed_variables = JSON.parse(variables);
    } catch (err) {
        try {
            parsed_variables = yaml.safeLoad(variables);
        } catch (err) {
            parsed_variables = {};
        }
    }
    if (parsed_variables === undefined) {
        return {};
    }
    return parsed_variables;
}
exports.parse_variables = parse_variables;


function noop () {
}
exports.noop = noop;

function natural_numbers (start) {
    var counter = start;
    return function () {return counter += 1;};
}
exports.natural_numbers = natural_numbers;


function distance (x1, y1, x2, y2) {

    return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}
exports.distance = distance;

// polarToCartesian
// @wdebeaum, @opsb
// from http://stackoverflow.com/questions/5736398/how-to-calculate-the-svg-path-for-an-arc-of-a-circle
function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
  var angleInRadians = (angleInDegrees-90) * Math.PI / 180.0;

  return {
    x: centerX + (radius * Math.cos(angleInRadians)),
    y: centerY + (radius * Math.sin(angleInRadians))
  };
}

// describeArc
// @wdebeaum, @opsb
// from http://stackoverflow.com/questions/5736398/how-to-calculate-the-svg-path-for-an-arc-of-a-circle
function describeArc(x, y, radius, startAngle, endAngle){

    var start = polarToCartesian(x, y, radius, endAngle);
    var end = polarToCartesian(x, y, radius, startAngle);

    var largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

    var d = [
        "M", start.x, start.y,
        "A", radius, radius, 0, largeArcFlag, 0, end.x, end.y
    ].join(" ");

    return d;
}
exports.describeArc = describeArc;

function pDistanceLine(x, y, x1, y1, x2, y2) {
  //Code from http://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment
  //Joshua
  // Find the dot product of two vectors <A, B>, <C, D>
  // Divide by the length squared of <C, D>
  // Use scalar project to find param
  //

  var A = x - x1;
  var B = y - y1;
  var C = x2 - x1;
  var D = y2 - y1;

  var dot = A * C + B * D;
  var len_sq = C * C + D * D;
  var param = -1;
  if (len_sq !== 0) {
      //in case of 0 length line
      param = dot / len_sq;
  }

  var xx, yy;

  //Find a point xx, yy where the projection and the <C, D> vector intersect.
  //If less than 0 use x1, y1 as the closest point.
  //If less than 1 use x2, y2 as the closest point.
  //If between 0 and 1 use the projection intersection xx, yy
  if (param < 0) {
    xx = x1;
    yy = y1;
  }
  else if (param > 1) {
    xx = x2;
    yy = y2;
  }
  else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  return {x1:x, y1:y, x2: xx, y2: yy};
}
exports.pDistanceLine = pDistanceLine;

function pDistance(x, y, x1, y1, x2, y2) {
  //Code from http://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment
  //Joshua
  // Find the dot product of two vectors <A, B>, <C, D>
  // Divide by the length squared of <C, D>
  // Use scalar project to find param
  //

  var A = x - x1;
  var B = y - y1;
  var C = x2 - x1;
  var D = y2 - y1;

  var dot = A * C + B * D;
  var len_sq = C * C + D * D;
  var param = -1;
  if (len_sq !== 0) {
      //in case of 0 length line
      param = dot / len_sq;
  }

  var xx, yy;

  //Find a point xx, yy where the projection and the <C, D> vector intersect.
  //If less than 0 use x1, y1 as the closest point.
  //If less than 1 use x2, y2 as the closest point.
  //If between 0 and 1 use the projection intersection xx, yy
  if (param < 0) {
    xx = x1;
    yy = y1;
  }
  else if (param > 1) {
    xx = x2;
    yy = y2;
  }
  else {
    xx = x1 + param * C;
    yy = y1 + param * D;
  }

  var dx = x - xx;
  var dy = y - yy;
  return Math.sqrt(dx * dx + dy * dy);
}
exports.pDistance = pDistance;


function cross_z_pos(x, y, x1, y1, x2, y2) {
  var A = x - x1;
  var B = y - y1;
  var C = x2 - x1;
  var D = y2 - y1;

  return math.cross([A, B, 0], [C, D, 0])[2] > 0;
}
exports.cross_z_pos = cross_z_pos;

function intersection (x1, y1, x2, y2, x3, y3, x4, y4) {
    //Find the point where lines through x1, y1, x2, y2 and x3, y3, x4, y4 intersect.
    //
    
    var Aslope;
    var Aintercept;
    var Bslope;
    var Bintercept;
    
    if ((x2 - x1) !== 0 && (x4 - x3) !== 0) {
        Aslope = (y2 - y1)/(x2 - x1);
        Aintercept = y1 - Aslope * x1;

        Bslope = (y4 - y3)/(x4 - x3);
        Bintercept = y3 - Bslope * x3;

        var xi = (Bintercept - Aintercept) / (Aslope - Bslope);
        var yi = Bslope * xi + Bintercept;
        return {x: xi, y: yi};
    }
    if ((x2 - x1) === 0 && (x4 - x3) === 0) {
        return {x: null, y: null};
    }
    if ((x2 - x1) === 0) {
        Bslope = (y4 - y3)/(x4 - x3);
        Bintercept = y3 - Bslope * x3;
        return {x: x1, y: Bslope * x1 + Bintercept};
    }
    if ((x4 - x3) === 0) {
        Aslope = (y2 - y1)/(x2 - x1);
        Aintercept = y1 - Aslope * x1;
        return {x: x3, y: Aslope * x3 + Aintercept};
    }
}
exports.intersection = intersection;


function pCase(x, y, x1, y1, x2, y2) {
  //Code from http://stackoverflow.com/questions/849211/shortest-distance-between-a-point-and-a-line-segment
  //Joshua
  // Find the dot product of two vectors <A, B>, <C, D>
  // Divide by the length squared of <C, D>
  // Use scalar project to find param
  //

  var A = x - x1;
  var B = y - y1;
  var C = x2 - x1;
  var D = y2 - y1;

  var dot = A * C + B * D;
  var len_sq = C * C + D * D;
  var param = -1;
  if (len_sq !== 0) {
      //in case of 0 length line
      param = dot / len_sq;
  }

  return param;
}
exports.pCase = pCase;
