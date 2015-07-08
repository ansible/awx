var jsdom = require('jsdom').jsdom;
var document = jsdom('tower');
var window = document.parentWindow;
var mocha = require('mocha');
window.mocha = mocha;
window.beforeEach = beforeEach;
window.afterEach = afterEach;

global.document = document;
global.window = window;

require('angular/angular');
var jquery = require('jquery');
require('angular-mocks/angular-mocks');

var chai = require('chai');
var expect = chai.expect;
var sinonChai = require('sinon-chai');
var chaiAsPromised = require('chai-as-promised');
var sinon = require('sinon');
var chaiThings = require('chai-things');

chai.use(sinonChai);
chai.use(chaiAsPromised);
chai.use(chaiThings);

global.$ = window.$ = jquery;
global.angular = window.angular;
global.expect = chai.expect;

angular.module('templates', []);
require('../../templates');

var lodash = require('lodash');
global._ = lodash;

var LocalStorage = require('node-localstorage').LocalStorage;
global.localStorage = window.localStorage = new LocalStorage('./scratch');

