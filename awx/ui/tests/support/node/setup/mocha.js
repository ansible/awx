var exportGlobal = require('../export-global');
var mocha = require('mocha');

exportGlobal('mocha', mocha);
exportGlobal('beforeEach', beforeEach);
exportGlobal('afterEach', afterEach);

