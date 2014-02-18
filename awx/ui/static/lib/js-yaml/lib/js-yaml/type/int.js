'use strict';


var Type = require('../type');


var YAML_INTEGER_PATTERN = new RegExp(
  '^(?:[-+]?0b[0-1_]+' +
  '|[-+]?0[0-7_]+' +
  '|[-+]?(?:0|[1-9][0-9_]*)' +
  '|[-+]?0x[0-9a-fA-F_]+' +
  '|[-+]?[1-9][0-9_]*(?::[0-5]?[0-9])+)$');


function resolveYamlInteger(state) {
  var value, sign, base, digits,
      object = state.result;

  if (!YAML_INTEGER_PATTERN.test(object)) {
    return false;
  }

  value  = object.replace(/_/g, '');
  sign   = '-' === value[0] ? -1 : 1;
  digits = [];

  if (0 <= '+-'.indexOf(value[0])) {
    value = value.slice(1);
  }

  if ('0' === value) {
    state.result = 0;
    return true;

  } else if (/^0b/.test(value)) {
    state.result = sign * parseInt(value.slice(2), 2);
    return true;

  } else if (/^0x/.test(value)) {
    state.result = sign * parseInt(value, 16);
    return true;

  } else if ('0' === value[0]) {
    state.result = sign * parseInt(value, 8);
    return true;

  } else if (0 <= value.indexOf(':')) {
    value.split(':').forEach(function (v) {
      digits.unshift(parseInt(v, 10));
    });

    value = 0;
    base = 1;

    digits.forEach(function (d) {
      value += (d * base);
      base *= 60;
    });

    state.result = sign * value;
    return true;

  } else {
    state.result = sign * parseInt(value, 10);
    return true;
  }
}


function isInteger(object) {
  return ('[object Number]' === Object.prototype.toString.call(object)) &&
         (0 === object % 1);
}


module.exports = new Type('tag:yaml.org,2002:int', {
  loadKind: 'scalar',
  loadResolver: resolveYamlInteger,
  dumpPredicate: isInteger,
  dumpRepresenter: {
    binary:      function (object) { return '0b' + object.toString(2); },
    octal:       function (object) { return '0'  + object.toString(8); },
    decimal:     function (object) { return        object.toString(10); },
    hexadecimal: function (object) { return '0x' + object.toString(16).toUpperCase(); }
  },
  dumpDefaultStyle: 'decimal',
  dumpStyleAliases: {
    binary:      [ 2,  'bin' ],
    octal:       [ 8,  'oct' ],
    decimal:     [ 10, 'dec' ],
    hexadecimal: [ 16, 'hex' ]
  }
});
