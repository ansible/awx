// Theme
require('~assets/custom-theme/jquery-ui-1.10.3.custom.min.css');
require('~assets/ansible-bootstrap.min.css');
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
require('bootstrap');
require('bootstrap-datepicker');
require('select2');

// Standalone libs
global._ = require('lodash');
require('moment');
require('rrule');
require('sprintf-js');
require('reconnectingwebsocket');

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
require('angular-md5');
require('angular-moment');
require('angular-scheduler');
require('angular-tz-extensions');
require('angular-ui-router');
require('angular-ui-router-state-events');
require('ng-toast-provider');
require('ng-toast-directives');
require('ng-toast');
require('lr-infinite-scroll');
