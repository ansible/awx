var exportGlobal = require('../export-global');
var jquery = require('jquery');

exportGlobal('$', jquery);
exportGlobal('jQuery', jquery);


