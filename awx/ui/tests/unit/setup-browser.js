/* jshint node: true */

var jsdom = require('jsdom').jsdom;
var document = jsdom('tower');
var window = document.parentWindow;
var mocha = require('mocha');
window.mocha = mocha;
window.beforeEach = beforeEach;
window.afterEach = afterEach;

global.document = document;
global.window = window;

var jquery = require('jquery');
global.$ = window.$ = global.jQuery = window.jQuery = jquery;

require('angular/angular');

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

global.angular = window.angular;
global.inject = window.inject;
global.expect = chai.expect;

angular.module('templates', []);
require('../../templates');

var d3 = require('d3');
global.d3 = d3;

var nv = require('nvd3');
global.nv = nv;

var lodash = require('lodash');
global._ = lodash;

var LocalStorage = require('node-localstorage').LocalStorage;
global.localStorage = window.localStorage = new LocalStorage('./scratch');

var moment = require('moment');
window.moment = moment;
