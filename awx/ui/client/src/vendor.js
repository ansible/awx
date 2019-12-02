// Theme
require('~assets/custom-theme/jquery-ui-1.10.3.custom.min.css');
require('~node_modules/bootstrap/dist/css/bootstrap.min.css');
require('~assets/fontcustom/fontcustom.css');
require('~node_modules/components-font-awesome/css/font-awesome.min.css');
require('~node_modules/select2/dist/css/select2.css');
require('~node_modules/codemirror/lib/codemirror.css');
require('~node_modules/codemirror/theme/elegant.css');
require('~node_modules/codemirror/addon/lint/lint.css');
require('~node_modules/nvd3/build/nv.d3.css');
require('~node_modules/ng-toast/dist/ngToast.min.css');

// jQuery + extensions
global.jQuery = require('jquery');

global.jquery = global.jQuery;
global.$ = global.jQuery;

require('jquery-resize');
require('jquery-ui');
require('jquery-ui/ui/widgets/button');
require('jquery-ui/ui/widgets/dialog');
require('jquery-ui/ui/widgets/slider');
require('jquery-ui/ui/widgets/spinner');
require('bootstrap');
require('popper.js');
require('bootstrap-datepicker');

// jquery-ui and bootstrap both define $.fn.button
// the code below resolves that namespace clash
const btn = $.fn.button.noConflict();
$.fn.btn = btn;

// Whitelist table elements so they can be used in popovers
$.fn.popover.Constructor.Default.whiteList.blockquote = [];
$.fn.popover.Constructor.Default.whiteList.table = [];
$.fn.popover.Constructor.Default.whiteList.th = [];
$.fn.popover.Constructor.Default.whiteList.tr = [];
$.fn.popover.Constructor.Default.whiteList.td = [];
$.fn.popover.Constructor.Default.whiteList.tbody = [];
$.fn.popover.Constructor.Default.whiteList.thead = [];

require('select2');

// Standalone libs
global._ = require('lodash');
require('moment');
require('rrule');
require('sprintf-js');
require('reconnectingwebsocket');
global.dagre = require('dagre');

// D3 + extensions
require('d3');
require('nvd3');

// Angular
require('angular');
require('angular-cookies');
require('angular-sanitize');
require('angular-breadcrumb');
require('angular-codemirror');
require('angular-drag-and-drop-lists');
require('angular-duration-format');
require('angular-gettext');
require('angular-moment');
require('angular-scheduler');
require('angular-tz-extensions');
require('@uirouter/angularjs');
require('ng-toast-provider');
require('ng-toast-directives');
require('ng-toast');
require('lr-infinite-scroll');
require('codemirror/mode/yaml/yaml');
require('codemirror/mode/javascript/javascript');
require('codemirror/mode/jinja2/jinja2');
