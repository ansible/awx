var jsdom = require('jsdom').jsdom;
var document = jsdom('tower');
var window = document.parentWindow;

global.document = document;
global.window = window;
