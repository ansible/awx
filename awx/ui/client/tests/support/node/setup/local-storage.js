var exportGlobal = require('../export-global');
var LocalStorage = require('node-localstorage').LocalStorage;

exportGlobal('localStorage',
             new LocalStorage('./scratch'));


