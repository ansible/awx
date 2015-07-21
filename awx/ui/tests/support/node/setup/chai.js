var exportGlobal = require('../export-global');
var chai = require('chai');

exportGlobal('chai', chai);
exportGlobal('expect', chai.expect);
