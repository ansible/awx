/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 */
  /**
 *  @ngdoc function
 *  @name lib.ansible.function:directives
 *  @description
 * Custom directives for form validation
 *
 */

'use strict';

/* global chkPass:false */

angular.module('AWDirectives', ['RestServices', 'Utilities', 'AuthService', 'JobsHelper'])

    // awpassmatch:  Add to password_confirm field. Will test if value
    //               matches that of 'input[name="password"]'
    .directive('awpassmatch', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift( function(viewValue) {
                    var associated = attrs.awpassmatch,
                        password = $('input[name="' + associated + '"]').val();
                    if (viewValue === password) {
                        // it is valid
                        ctrl.$setValidity('awpassmatch', true);
                        return viewValue;
                    }
                    // Invalid, return undefined (no model update)
                    ctrl.$setValidity('awpassmatch', false);
                    return undefined;
                });
            }
        };
    })

    // caplitalize  Add to any input field where the first letter of each
    //              word should be capitalized. Use in place of css test-transform.
    //              For some reason "text-transform: capitalize" in breadcrumbs
    //              causes a break at each blank space. And of course,
    //              "autocapitalize='word'" only works in iOS. Use this as a fix.
    .directive('capitalize', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift( function(viewValue) {
                    var values = viewValue.split(" "),
                        result = "", i;
                    for (i = 0; i < values.length; i++){
                        result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
                    }
                    result = result.trim();
                    if (result !== viewValue) {
                        ctrl.$setViewValue(result);
                        ctrl.$render();
                    }
                    return result;
                });
            }
        };
    })

    // caplitalize  Add to any input field where the first letter of each
    //              word should be capitalized. Use in place of css test-transform.
    //              For some reason "text-transform: capitalize" in breadcrumbs
    //              causes a break at each blank space. And of course,
    //              "autocapitalize='word'" only works in iOS. Use this as a fix.
    .directive('awSurveyQuestion', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift( function(viewValue) {
                    var values = viewValue.split(" "),
                        result = "", i;
                    result += values[0].charAt(0).toUpperCase() + values[0].substr(1) + ' ';
                    for (i = 1; i < values.length; i++){
                        result += values[i] + ' ';
                    }
                    result = result.trim();
                    if (result !== viewValue) {
                        ctrl.$setViewValue(result);
                        ctrl.$render();
                    }
                    return result;
                });
            }
        };
    })

    .directive('ngMin', ['Empty', function (Empty) {
        return {
            restrict: 'A',
            require: 'ngModel',
            link: function (scope, elem, attr, ctrl) {
                scope.$watch(attr.ngMin, function () {
                    ctrl.$setViewValue(ctrl.$viewValue);
                });
                var minValidator = function (value) {
                    var min = (!attr.ngMin===false) ? scope.$eval(attr.ngMin)  :  -Infinity;
                    if (!Empty(value) && Number(value) < min) {
                        ctrl.$setValidity('ngMin', false);
                        return undefined;
                    } else {
                        ctrl.$setValidity('ngMin', true);
                        return value;
                    }
                };

                ctrl.$parsers.push(minValidator);
                ctrl.$formatters.push(minValidator);
            }
        };
    }])

    .directive('ngMax', ['Empty', function (Empty) {
        return {
            restrict: 'A',
            require: 'ngModel',
            link: function (scope, elem, attr, ctrl) {
                scope.$watch(attr.ngMax, function () {
                    ctrl.$setViewValue(ctrl.$viewValue);
                });
                var maxValidator = function (value) {
                    var max = scope.$eval(attr.ngMax) || Infinity;
                    if (!Empty(value) && Number(value) > max) {
                        ctrl.$setValidity('ngMax', false);
                        return undefined;
                    } else {
                        ctrl.$setValidity('ngMax', true);
                        return value;
                    }
                };

                ctrl.$parsers.push(maxValidator);
                ctrl.$formatters.push(maxValidator);
            }
        };
    }])


    .directive('smartFloat', function() {
        var FLOAT_REGEXP = /^\-?\d+((\.|\,)\d+)?$/;
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift(function(viewValue) {
                    if (FLOAT_REGEXP.test(viewValue)) {
                        ctrl.$setValidity('float', true);
                        return parseFloat(viewValue.replace(',', '.'));
                    } else {
                        ctrl.$setValidity('float', false);
                        return undefined;
                    }
                });
            }
        };
    })

    // integer  Validate that input is of type integer. Taken from Angular developer
    //          guide, form examples. Add min and max directives, and this will check
    //          entered values is within the range.
    //
    //          Use input type of 'text'. Use of 'number' casuses browser validation to
    //          override/interfere with this directive.
    .directive('integer', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift(function(viewValue) {
                    ctrl.$setValidity('min', true);
                    ctrl.$setValidity('max', true);
                    if (/^\-?\d*$/.test(viewValue)) {
                       // it is valid
                        ctrl.$setValidity('integer', true);
                        if ( elm.attr('min') &&
                            ( viewValue === '' || viewValue === null || parseInt(viewValue,10) < parseInt(elm.attr('min'),10) ) ) {
                            ctrl.$setValidity('min', false);
                            return undefined;
                        }
                        if ( elm.attr('max') && ( parseInt(viewValue,10) > parseInt(elm.attr('max'),10) ) ) {
                            ctrl.$setValidity('max', false);
                            return undefined;
                        }
                        return viewValue;
                    }
                    // Invalid, return undefined (no model update)
                    ctrl.$setValidity('integer', false);
                    return undefined;
                });
            }
        };
    })

    //
    // awRequiredWhen: { variable: "<variable to watch for true|false>", init:"true|false" }
    //
    // Make a field required conditionally using a scope variable. If the scope variable is true, the
    // field will be required. Otherwise, the required attribute will be removed.
    //
    .directive('awRequiredWhen', function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {

                function checkIt () {
                    var viewValue = elm.val(), label, validity = true;
                    if ( scope[attrs.awRequiredWhen] && (elm.attr('required') === null || elm.attr('required') === undefined) ) {
                        $(elm).attr('required','required');
                        if ($(elm).hasClass('lookup')) {
                            $(elm).parent().parent().parent().find('label').first().addClass('prepend-asterisk');
                        }
                        else {
                            $(elm).parent().parent().find('label').first().addClass('prepend-asterisk');
                        }
                    }
                    else if (!scope[attrs.awRequiredWhen]) {
                        elm.removeAttr('required');
                        if ($(elm).hasClass('lookup')) {
                            label = $(elm).parent().parent().parent().find('label').first();
                            label.removeClass('prepend-asterisk');
                        }
                        else {
                            $(elm).parent().parent().find('label').first().removeClass('prepend-asterisk');
                        }
                    }
                    if (scope[attrs.awRequiredWhen] && (viewValue === undefined || viewValue === null || viewValue === '')) {
                        validity = false;
                    }
                    ctrl.$setValidity('required', validity);
                }

                if (attrs.awrequiredInit !== undefined && attrs.awrequiredInit !== null) {
                    scope[attrs.awRequiredWhen] = attrs.awrequiredInit;
                    checkIt();
                }

                scope.$watch(attrs.awRequiredWhen, function() {
                    // watch for the aw-required-when expression to change value
                    checkIt();
                });

                scope.$watch($(elm).attr('name'), function() {
                    // watch for the field to change value
                    checkIt();
                });
            }
        };
    })

    // awPlaceholder: Dynamic placeholder set to a scope variable you want watched.
    //                Value will be place in field placeholder attribute.
    .directive('awPlaceholder', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs) {
                $(elm).attr('placeholder', scope[attrs.awPlaceholder]);
                scope.$watch(attrs.awPlaceholder, function(newVal) {
                    $(elm).attr('placeholder',newVal);
                });
            }
        };
    }])

    // lookup   Validate lookup value against API
    //
    .directive('awlookup', ['Rest', function(Rest) {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift( function(viewValue) {
                    if (viewValue !== '' && viewValue !== null) {
                        var url = elm.attr('data-url');
                        url = url.replace(/\:value/, encodeURI(viewValue));
                        scope[elm.attr('data-source')] = null;
                        Rest.setUrl(url);
                        Rest.get().then( function(data) {
                            var results = data.data.results;
                            if (results.length > 0) {
                                scope[elm.attr('data-source')] = results[0].id;
                                scope[elm.attr('name')] = results[0].name;
                                ctrl.$setValidity('required', true);
                                ctrl.$setValidity('awlookup', true);
                                return viewValue;
                            }
                            ctrl.$setValidity('required', true);
                            ctrl.$setValidity('awlookup', false);
                            return undefined;
                        });
                    }
                    else {
                        ctrl.$setValidity('awlookup', true);
                        scope[elm.attr('data-source')] = null;
                    }
                });
            }
        };
    }])

    //
    // awValidUrl
    //
    .directive('awValidUrl', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                ctrl.$parsers.unshift( function(viewValue) {
                    var validity = true, rgx, rgx2;
                    if (viewValue !== '') {
                        ctrl.$setValidity('required', true);
                        rgx = /^(https|http|ssh)\:\/\//;
                        rgx2 = /\@/g;
                        if (!rgx.test(viewValue) || rgx2.test(viewValue)) {
                            validity = false;
                        }
                    }
                    ctrl.$setValidity('awvalidurl', validity);
                });
            }
        };
    }])

    /*
     *  Enable TB tooltips. To add a tooltip to an element, include the following directive in
     *  the element's attributes:
     *
     *     aw-tool-tip="<< tooltip text here >>"
     *
     *  Include the standard TB data-XXX attributes to controll a tooltip's appearance.  We will
     *  default placement to the left and delay to the config setting.
     */
    .directive('awToolTip', function() {
        return function(scope, element, attrs) {
            var delay = (attrs.delay !== undefined && attrs.delay !== null) ? attrs.delay : ($AnsibleConfig) ? $AnsibleConfig.tooltip_delay : {show: 500, hide: 100},
                placement;
            if (attrs.awTipPlacement) {
                placement = attrs.awTipPlacement;
            }
            else {
                placement = (attrs.placement !== undefined && attrs.placement !== null) ? attrs.placement : 'left';
            }

            $(element).on('hidden.bs.tooltip', function( ) {
                // TB3RC1 is leaving behind tooltip <div> elements. This will remove them
                // after a tooltip fades away. If not, they lay overtop of other elements and
                // honk up the page.
                $('.tooltip').each(function() {
                    $(this).remove();
                });
            });

            $(element).tooltip({
                placement: placement,
                delay: delay,
                html: true,
                title: attrs.awToolTip,
                container: 'body',
                trigger: 'hover focus'
            });

            if (attrs.tipWatch) {
                // Add dataTipWatch: 'variable_name'
                scope.$watch(attrs.tipWatch, function(newVal, oldVal) {
                    if (newVal !== oldVal) {
                        // Where did fixTitle come from?:
                        //   http://stackoverflow.com/questions/9501921/change-twitter-bootstrap-tooltip-content-on-click
                        $(element).tooltip('hide').attr('data-original-title', newVal).tooltip('fixTitle');
                    }
                });
            }
        };
    })

    /*
     *  Enable TB pop-overs. To add a pop-over to an element, include the following directive in
     *  the element's attributes:
     *
     *     aw-pop-over="<< pop-over html here >>"
     *
     *  Include the standard TB data-XXX attributes to controll the pop-over's appearance.  We will
     *  default placement to the left, delay to 0 seconds, content type to HTML, and title to 'Help'.
     */
    .directive('awPopOver', ['$compile', function($compile) {
        return function(scope, element, attrs) {
            var placement = (attrs.placement !== undefined && attrs.placement !== null) ? attrs.placement : 'left',
                title = (attrs.title) ? attrs.title : (attrs.popoverTitle) ? attrs.popoverTitle : 'Help',
                container = (attrs.container !== undefined) ? attrs.container : false,
                trigger = (attrs.trigger !== undefined) ? attrs.trigger : 'manual';
            if (attrs.awPopOverWatch) {
                $(element).popover({
                    placement: placement,
                    delay: 0,
                    title: title,
                    content: function() {
                        return scope[attrs.awPopOverWatch];
                    },
                    trigger: trigger,
                    html: true,
                    container: container
                });
            } else {
                $(element).popover({
                    placement: placement,
                    delay: 0,
                    title: title,
                    content: attrs.awPopOver,
                    trigger: trigger,
                    html: true,
                    container: container
                });
            }
            $(element).attr('tabindex',-1);
            $(element).click(function() {
                var self = $(this);
                try {
                    self.tooltip('hide');
                }
                catch(e) {
                    // ignore
                }
                $('.help-link, .help-link-white').each( function() {
                    if (self.attr('id') !== $(this).attr('id')) {
                        try {
                            $(this).popover('hide');
                        }
                        catch(e) {
                            // ignore
                        }
                    }
                });
                $('.popover').each(function() {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    $(this).remove();
                });
                $('.tooltip').each( function() {
                    // close any lingering tool tipss
                    $(this).hide();
                });
                $(this).popover('toggle');
                $('.popover').each(function() {
                    $compile($(this))(scope);  //make nested directives work!
                });
                $('.popover-content, .popover-title').click(function() {
                    $(self).popover('hide');
                });
            });

            $(document).bind('keydown', function(e) {
                if (e.keyCode === 27) {
                    $(element).popover('hide');
                    $('.popover').each(function() {
                        // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                        $(this).remove();
                    });
                }
            });
        };
    }])

    //
    // Enable jqueryui slider widget on a numeric input field
    //
    // <input type="number" aw-slider name="myfield" min="0" max="100" />
    //
    .directive('awSlider', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                var name = elm.attr('name');
                $('#' + name + '-slider').slider({
                    value: 0,
                    step: 1,
                    min: elm.attr('min'),
                    max: elm.attr('max'),
                    disabled: (elm.attr('readonly')) ? true : false,
                    slide: function(e,u) {
                        ctrl.$setViewValue(u.value);
                        ctrl.$setValidity('required',true);
                        ctrl.$setValidity('min', true);
                        ctrl.$setValidity('max', true);
                        ctrl.$dirty = true;
                        ctrl.$render();
                        if (!scope.$$phase) {
                            scope.$digest();
                        }
                    }
                });

                $('#' + name + '-number').change( function() {
                    $('#' + name + '-slider').slider('value', parseInt($(this).val(),10));
                });

            }
        };
    }])

    .directive('awMultiSelect', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm) {
                $(elm).multiselect  ({
                    buttonClass: 'btn-default, btn-mini',
                    buttonWidth: 'auto',
                    buttonContainer: '<div class="btn-group" />',
                    maxHeight: false,
                    buttonText: function(options) {
                        if (options.length === 0) {
                            return 'None selected <b class="caret"></b>';
                        }
                        if (options.length > 3) {
                            return options.length + ' selected  <b class="caret"></b>';
                        }
                        var selected = '';
                        options.each(function() {
                            selected += $(this).text() + ', ';
                        });
                        return selected.substr(0, selected.length -2) + ' <b class="caret"></b>';
                    }
                });
            }
        };
    }])

    //
    // Enable jqueryui spinner widget on a numeric input field
    //
    // <input type="number" aw-spinner name="myfield" min="0" max="100" />
    //
    .directive('awSpinner', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                var disabled, opts;
                disabled = elm.attr('data-disabled');
                opts = {
                    value: 0,
                    step: 1,
                    min: elm.attr('min'),
                    max: elm.attr('max'),
                    numberFormat: "d",
                    disabled: (elm.attr('readonly')) ? true : false,
                    spin: function(e, u) {
                        ctrl.$setViewValue(u.value);
                        ctrl.$setValidity('required',true);
                        ctrl.$setValidity('min', true);
                        ctrl.$setValidity('max', true);
                        ctrl.$dirty = true;
                        ctrl.$render();
                        if (scope.job_templates_form) {
                            // need a way to find the parent form and mark it dirty
                            scope.job_templates_form.$dirty = true;
                        }
                        if (!scope.$$phase) {
                            scope.$digest();
                        }
                    }
                };
                if (disabled) {
                    opts.disabled = true;
                }
                $(elm).spinner(opts);
                $(elm).on("click", function () {
                    $(elm).select();
                });
            }
        };
    }])

    //
    // chkPass
    //
    // Enables use of lib/ansible/pwdmeter.js to check strengh of passwords.
    // See controllers/Users.js for example.
    //
    .directive('chkPass', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, elm, attrs, ctrl) {
                $(elm).keyup(function() {
                    var validity = true,
                        score = chkPass(elm.val());
                    if (elm.val()) {
                        validity = (score > $AnsibleConfig.password_strength) ? true : false;
                    }
                    ctrl.$setValidity('complexity', validity);
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                });
            }
        };
    }])

    //
    // awRefresh
    //
    // Creates a timer to call scope.refresh(iterator) ever N seconds, where
    // N is a setting in config.js
    //
    .directive('awRefresh', [ '$rootScope', function($rootScope) {
        return {
            link: function(scope) {
                function msg() {
                    var num = '' + scope.refreshCnt;
                    while (num.length < 2) {
                        num = '0' + num;
                    }
                    return 'Refresh in ' + num + ' sec.';
                }
                scope.refreshCnt = $AnsibleConfig.refresh_rate;
                scope.refreshMsg = msg();
                if ($rootScope.timer) {
                    clearInterval($rootScope.timer);
                }
                $rootScope.timer = setInterval( function() {
                    scope.refreshCnt--;
                    if (scope.refreshCnt <= 0) {
                        scope.refresh();
                        scope.refreshCnt = $AnsibleConfig.refresh_rate;
                    }
                    scope.refreshMsg = msg();
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                }, 1000);
            }
        };
    }])


    /*
       awMultiSelect
       Relies on select2.js to create a multi-select with tags.
    */
    .directive('awMultiselect', [ function() {
        return {
            require: '^form',  //inject the form into the ctrl parameter
            link: function(scope, elm, attrs, ctrl) {
                $(elm).select2({
                    multiple: true,
                    data: function() {
                        // dynamically load the possible values
                        if (scope[attrs.awMultiselect]) {
                            var set = scope[attrs.awMultiselect],
                                opts = [], i;
                            for (i=0; i < set.length; i++) {
                                opts.push({ id: set[i].value, text: set[i].label });
                            }
                            return {results: opts };
                        }
                        return {results: { id: '', text: ''} };
                    }
                });

                // Make sure the form buttons enable when the value changes
                $(elm).on('change', function() {
                    ctrl.$setDirty();
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                });
            }
        };
    }])


    /*
     *  Make an element draggable. Used on inventory groups tree.
     *
     *  awDraggable: boolean || {{ expression }}
     *
     */
    .directive('awDraggable', [ function() {
        return function(scope, element, attrs) {

            if (attrs.awDraggable === "true") {
                var containment = attrs.containment;  //provide dataContainment:"#id"
                $(element).draggable({
                    containment: containment,
                    scroll: true,
                    revert: "invalid",
                    helper: "clone",
                    start: function(e, ui) {
                        ui.helper.addClass('draggable-clone');
                    },
                    zIndex: 100,
                    cursorAt: { left: -1 }
                });
            }
        };
    }])

    /*
     *  Make an element droppable- it can receive draggable elements
     *
     *  awDroppable: boolean || {{ expression }}
     *
     */
    .directive('awDroppable', ['Find', function(Find) {
        return function(scope, element, attrs) {
            var node;
            if (attrs.awDroppable === "true") {
                $(element).droppable({
                    // the following is inventory specific accept checking and
                    // drop processing.
                    accept: function(draggable) {
                        if (draggable.attr('data-type') === 'group') {
                            // Dropped a group
                            if ($(this).attr('data-group-id') === draggable.attr('data-group-id')) {
                                // No dropping a node onto itself (or a copy)
                                return false;
                            }
                            // No dropping a node into a group that already has the node
                            node = Find({ list: scope.groups, key: 'id', val: parseInt($(this).attr('data-tree-id'),10) });
                            if (node) {
                                var group = parseInt(draggable.attr('data-group-id'),10),
                                    found = false, i;
                                // For whatever reason indexOf() would not work...
                                for (i=0; i < node.children.length; i++) {
                                    if (node.children[i] === group) {
                                        found = true;
                                        break;
                                    }
                                }
                                return (found) ? false : true;
                            }
                            return false;
                        }
                        if (draggable.attr('data-type') === 'host') {
                            // Dropped a host
                            node = Find({ list: scope.groups, key: 'id', val: parseInt($(this).attr('data-tree-id'),10) });
                            return (node.id > 1) ? true : false;
                        }
                        return false;
                    },
                    over: function() {
                        $(this).addClass('droppable-hover');
                    },
                    out: function() {
                        $(this).removeClass('droppable-hover');
                    },
                    drop: function(e, ui) {
                        // Drag-n-drop succeeded. Trigger a response from the inventory.edit controller
                        $(this).removeClass('droppable-hover');
                        if (ui.draggable.attr('data-type') === 'group') {
                            scope.$emit('CopyMoveGroup', parseInt(ui.draggable.attr('data-tree-id'),10),
                                parseInt($(this).attr('data-tree-id'),10));
                        }
                        else if (ui.draggable.attr('data-type') === 'host') {
                            scope.$emit('CopyMoveHost', parseInt($(this).attr('data-tree-id'),10),
                                parseInt(ui.draggable.attr('data-host-id'),10));
                        }
                    },
                    tolerance: 'pointer'
                });
            }
        };
    }])


    .directive('awAccordion', ['Empty', '$location', 'Store', function(Empty, $location, Store) {
        return function(scope, element, attrs) {
            var active,
                list = Store('accordions'),
                id, base;

            if (!Empty(attrs.openFirst)) {
                active = 0;
            }
            else {
                // Look in storage for last active panel
                if (list) {
                    id = $(element).attr('id');
                    base = ($location.path().replace(/^\//, '').split('/')[0]);
                    list.every(function(elem) {
                        if (elem.base === base && elem.id === id) {
                            active = elem.active;
                            return false;
                        }
                        return true;
                    });
                }
                active = (Empty(active)) ? 0 : active;
            }

            $(element).accordion({
                collapsible: true,
                heightStyle: "content",
                active: active,
                activate: function() {
                    // When a panel is activated update storage
                    var active = $(this).accordion('option', 'active'),
                        id = $(this).attr('id'),
                        base = ($location.path().replace(/^\//, '').split('/')[0]),
                        list = Store('accordions'),
                        found = false;
                    if (!list) {
                        list = [];
                    }
                    list.every(function(elem) {
                        if (elem.base === base && elem.id === id) {
                            elem.active = active;
                            found = true;
                            return false;
                        }
                        return true;
                    });
                    if (found === false) {
                        list.push({
                            base: base,
                            id: id,
                            active: active
                        });
                    }
                    Store('accordions', list);
                }
            });
        };
    }])

    // Toggle switch inspired by http://www.bootply.com/92189
    .directive('awToggleButton', [ function() {
        return function(scope, element) {
            $(element).click(function() {
                var next, choice;
                $(this).find('.btn').toggleClass('active');
                if ($(this).find('.btn-primary').size()>0) {
                    $(this).find('.btn').toggleClass('btn-primary');
                }
                if ($(this).find('.btn-danger').size()>0) {
                    $(this).find('.btn').toggleClass('btn-danger');
                }
                if ($(this).find('.btn-success').size()>0) {
                    $(this).find('.btn').toggleClass('btn-success');
                }
                if ($(this).find('.btn-info').size()>0) {
                    $(this).find('.btn').toggleClass('btn-info');
                }
                $(this).find('.btn').toggleClass('btn-default');

                // Add data-after-toggle="functionName" to the btn-group, and we'll
                // execute here. The newly active choice is passed as a parameter.
                if ($(this).attr('data-after-toggle')) {
                    next = $(this).attr('data-after-toggle');
                    choice = $(this).find('.active').text();
                    setTimeout(function() {
                        scope.$apply(function() {
                            scope[next](choice);
                        });
                    });
                }

            });
        };
    }])

    //
    // Support dropping files on an element. Used on credentials page for SSH/RSA private keys
    // Inspired by https://developer.mozilla.org/en-US/docs/Using_files_from_web_applications
    //
    .directive('awDropFile', ['Alert', function(Alert) {
        return {
            require: 'ngModel',
            link: function(scope, element, attrs, ctrl) {
                $(element).on('dragenter', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                });
                $(element).on('dragover', function(e) {
                    e.stopPropagation();
                    e.preventDefault();
                });
                $(element).on('drop', function(e) {
                    var dt, files, reader;
                    e.stopPropagation();
                    e.preventDefault();
                    dt = e.originalEvent.dataTransfer;
                    files = dt.files;
                    reader = new FileReader();
                    reader.onload = function() {
                        ctrl.$setViewValue(reader.result);
                        ctrl.$render();
                        ctrl.$setValidity('required',true);
                        ctrl.$dirty = true;
                        if (!scope.$$phase) {
                            scope.$digest();
                        }
                    };
                    reader.onerror = function() {
                        Alert('Error','There was an error reading the selected file.');
                    };
                    if(files[0].size<10000){
                        reader.readAsText(files[0]);
                    }
                    else {
                        Alert('Error','There was an error reading the selected file.');
                    }
                });
            }
        };
    }]);
