/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


/**
 *  @ngdoc function
 *  @name shared.function:directives
 *  @description
 * Custom directives for form validation
 *
 */

export default
angular.module('AWDirectives', ['RestServices', 'Utilities'])

// awpassmatch:  Add to password_confirm field. Will test if value
//               matches that of 'input[name="password"]'
.directive('awpassmatch', function() {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var associated = attrs.awpassmatch,
                    password = $('input[name="' + associated + '"]').val();
                if (viewValue === password) {
                    // it is valid
                    ctrl.$setValidity('awpassmatch', true);
                    return viewValue;
                }
                // Invalid, return undefined (no model update)
                ctrl.$setValidity('awpassmatch', false);
                return viewValue;
            });
        }
    };
})

// capitalize  Add to any input field where the first letter of each
//              word should be capitalized. Use in place of css test-transform.
//              For some reason "text-transform: capitalize" in breadcrumbs
//              causes a break at each blank space. And of course,
//              "autocapitalize='word'" only works in iOS. Use this as a fix.
.directive('capitalize', function() {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var values = viewValue.split(" "),
                    result = "",
                    i;
                for (i = 0; i < values.length; i++) {
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

// stringToNumber
//
// If your model does not contain actual numbers then this directive
// will do the conversion in the ngModel $formatters and $parsers pipeline.
//
.directive('stringToNumber', function() {
    return {
        require: 'ngModel',
        restrict: 'A',
        link: function(scope, element, attrs, ngModel) {
            ngModel.$parsers.push(value => value.toFixed(2));
            ngModel.$formatters.push(value => parseFloat(value));
        }
    };
})

// imageUpload
//
// Accepts image and returns base64 information with basic validation
// Can eventually expand to handle all uploads with different endpoints and handlers
//
.directive('imageUpload', ['SettingsUtils', 'i18n', '$rootScope',
function(SettingsUtils, i18n, $rootScope) {
    var browseText = i18n._('BROWSE'),
    placeholderText = i18n._('Choose file'),
    uploadedText = i18n._('Current Image: '),
    removeText = i18n._('REMOVE');

    return {
        restrict: 'E',
        scope: {
            key: '@'
        },
        template: `
                <div class="input-group">
                    <span class="input-group-btn input-group-prepend">
                        <label class="btn Form-browseButton" id="filePickerButton" for="filePicker" ng-click="update($event)">${browseText}</label>
                    </span>
                    <input type="text" class="form-control Form-filePicker--textBox" id="filePickerText" placeholder="${placeholderText}" readonly>
                    <input type="file" name="file" class="Form-filePicker" id="filePicker"  onchange="angular.element(this).scope().fileChange(this.files)"/>
                </div>

                <div ng-if="imagePresent" class="Form-filePicker--selectedFile">
                ${uploadedText}
                    <img data-ng-src="{{imageData}}" alt="Current logo" class="Form-filePicker--thumbnail">
                </div>

                <div class="error" id="filePickerError"></div>`,

        link: function(scope) {
            var fieldKey = scope.key;
            var filePickerText = angular.element(document.getElementById('filePickerText'));
            var filePickerError = angular.element(document.getElementById('filePickerError'));
            var filePickerButton = angular.element(document.getElementById('filePickerButton'));
            var filePicker = angular.element(document.getElementById('filePicker'));

            scope.imagePresent = global.$AnsibleConfig.custom_logo || false;
            scope.imageData = $rootScope.custom_logo;

            scope.$on('loginUpdated', function() {
                scope.imagePresent = global.$AnsibleConfig.custom_logo;
                scope.imageData = $rootScope.custom_logo;
            });

            scope.$watch('imagePresent', (val) => {
                if(val){
                    filePickerButton.html(removeText);
                }
                else{
                    filePickerButton.html(browseText);
                }
            });

            scope.$on(fieldKey+'_reverted', function(e) {
                scope.update(e, true);
            });

            scope.update = function(e, flag) {
                if(scope.$parent[fieldKey] || flag ) {
                    e.preventDefault();
                    scope.$parent[fieldKey] = '';
                    filePickerButton.html(browseText);
                    filePickerText.val('');
                    filePicker.context.value = "";
                    scope.imagePresent = false;
                }
                else {
                    // Nothing exists so open file picker
                }
            };

            scope.fileChange = function(file) {
                filePickerError.html('');

                SettingsUtils.imageProcess(file[0])
                    .then(function(result) {
                        scope.$parent[fieldKey] = result;
                        filePickerText.val(file[0].name);
                        filePickerButton.html(removeText);
                    }).catch(function(error) {
                        filePickerText.html(file[0].name);
                        filePickerError.text(error);
                    }).finally(function() {

                    });
            };

        }
    };
}])


.directive('surveyCheckboxes', function() {
    return {
        restrict: 'E',
        require: 'ngModel',
        scope: { ngModel: '=ngModel' },
        template: '<div class="survey_taker_input" ng-repeat="option in ngModel.options">' +
            '<label style="font-weight:normal"><input type="checkbox" ng-model="cbModel[option.value]" ' +
            'value="{{option.value}}" class="mc" ng-change="update(this.value)" />' +
            '<span>' +
            '{{option.value}}' +
            '</span></label>' +
            '</div>',
        link: function(scope, element, attrs, ctrl) {
            scope.cbModel = {};
            ctrl.$setValidity('reqCheck', true);
            angular.forEach(scope.ngModel.value, function(value) {
                scope.cbModel[value] = true;

            });

            if (scope.ngModel.required === true && scope.ngModel.value.length === 0) {
                ctrl.$setValidity('reqCheck', false);
            }

            ctrl.$parsers.unshift(function(viewValue) {
                for (var c in scope.cbModel) {
                    if (scope.cbModel[c]) {
                        ctrl.$setValidity('checkbox', true);
                    }
                }
                ctrl.$setValidity('checkbox', false);

                return viewValue;
            });

            scope.update = function() {
                var val = [];
                angular.forEach(scope.cbModel, function(v, k) {
                    if (v) {
                        val.push(k);
                    }
                });
                if (val.length > 0) {
                    scope.ngModel.value = val;
                    scope.$parent[scope.ngModel.name] = val;
                    ctrl.$setValidity('checkbox', true);
                    ctrl.$setValidity('reqCheck', true);
                } else if (scope.ngModel.required === true) {
                    ctrl.$setValidity('checkbox', false);
                }
            };
        }
    };
})

// the disableRow directive disables table row click events
.directive('disableRow', function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            element.bind('click', function(event) {
                if (scope.$eval(attrs.disableRow)) {
                    event.preventDefault();
                }
                return;
            });
        }
    };
})


.directive('awSurveyQuestion', function() {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var values = viewValue.split(" "),
                    result = "",
                    i;
                result += values[0].charAt(0).toUpperCase() + values[0].substr(1) + ' ';
                for (i = 1; i < values.length; i++) {
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

.directive('awMin', ['Empty', function(Empty) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elem, attr, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var min = (attr.awMin) ? scope.$eval(attr.awMin) : -Infinity;
                if (!Empty(min) && !Empty(viewValue) && Number(viewValue) < min) {
                    ctrl.$setValidity('awMin', false);
                    return viewValue;
                } else {
                    ctrl.$setValidity('awMin', true);
                    return viewValue;
                }
            });
        }
    };
}])

.directive('awMax', ['Empty', function(Empty) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elem, attr, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var max = (attr.awMax) ? scope.$eval(attr.awMax) : Infinity;
                if (!Empty(max) && !Empty(viewValue) && Number(viewValue) > max) {
                    ctrl.$setValidity('awMax', false);
                    return viewValue;
                } else {
                    ctrl.$setValidity('awMax', true);
                    return viewValue;
                }
            });
        }
    };
}])

.directive('awRange', ['Empty', function(Empty) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elem, attr, ctrl) {

            let checkRange = function(viewValue){
                ctrl.$setValidity('awRangeMin', true);
                ctrl.$setValidity('awRangeMax', true);
                var max = (attr.rangeMax) ? scope.$eval(attr.rangeMax) : Infinity;
                var min = (attr.rangeMin) ? scope.$eval(attr.rangeMin) : -Infinity;
                if (!Empty(max) && !Empty(viewValue) && Number(viewValue) > max) {
                    ctrl.$setValidity('awRangeMax', false);
                }
                else if(!Empty(min) && !Empty(viewValue) && Number(viewValue) < min) {
                    ctrl.$setValidity('awRangeMin', false);
                }
                return viewValue;
            };

            scope.$watch(attr.rangeMin, function () {
                checkRange(scope.$eval(attr.ngModel));
            });

            scope.$watch(attr.rangeMax, function () {
                checkRange(scope.$eval(attr.ngModel));
            });

            ctrl.$parsers.unshift(function(viewValue) {
                return checkRange(viewValue);
            });
        }
    };
}])

.directive('smartFloat', function() {
    var FLOAT_REGEXP = /(^\-?\d+)?((\.|\,)\d+)?$/;
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                if (viewValue === '' || FLOAT_REGEXP.test(viewValue)) {
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
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                ctrl.$setValidity('min', true);
                ctrl.$setValidity('max', true);
                if (/^\-?\d*$/.test(viewValue)) {
                    // it is valid
                    ctrl.$setValidity('integer', true);
                    if (viewValue === '-' || viewValue === '-0' || viewValue === null) {
                        ctrl.$setValidity('integer', false);
                        return viewValue;
                    }
                    if (elm.attr('min') &&
                        parseInt(viewValue, 10) < parseInt(elm.attr('min'), 10)) {
                        ctrl.$setValidity('min', false);
                        return viewValue;
                    }
                    if (elm.attr('max') && (parseInt(viewValue, 10) > parseInt(elm.attr('max'), 10))) {
                        ctrl.$setValidity('max', false);
                        return viewValue;
                    }
                    return viewValue;
                }
                // Invalid, return undefined (no model update)
                ctrl.$setValidity('integer', false);
                return viewValue;
            });
        }
    };
})

//the awSurveyVariableName directive checks if the field contains any spaces.
// this could be elaborated in the future for other things we want to check this field against
.directive('awSurveyVariableName', function() {
    var FLOAT_REGEXP = /^[a-zA-Z_$][0-9a-zA-Z_$]*$/;
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$setValidity('required', true); // we only want the error message for incorrect characters to be displayed
            ctrl.$parsers.unshift(function(viewValue) {
                if (viewValue.length !== 0) {
                    if (FLOAT_REGEXP.test(viewValue) && viewValue.indexOf(' ') === -1) { //check for a spaces
                        ctrl.$setValidity('variable', true);
                        return viewValue;
                    } else {
                        ctrl.$setValidity('variable', false); // spaces found, therefore throw error.
                        return viewValue;
                    }
                } else {
                    ctrl.$setValidity('variable', true); // spaces found, therefore throw error.
                    return viewValue;
                }
            });
        }
    };
})

//
// awRequiredWhen: { reqExpression: "<expression to watch for true|false>", init: "true|false" }
//
// Make a field required conditionally using an expression. If the expression evaluates to true, the
// field will be required. Otherwise, the required attribute will be removed.
//
.directive('awRequiredWhen', function() {
    return {
        require: 'ngModel',
        compile: function(tElem) {
            return {
                pre: function preLink() {
                    let label = $(tElem).closest('.form-group').find('label').first();
                    $(label).prepend('<span class="Form-requiredAsterisk">*</span>');
                },
                post: function postLink( scope, elm, attrs, ctrl ) {
                    function updateRequired() {
                        var isRequired = scope.$eval(attrs.awRequiredWhen);

                        var viewValue = elm.val(),
                            label, validity = true;
                        label = $(elm).closest('.form-group').find('label').first();

                        if (isRequired && (elm.attr('required') === null || elm.attr('required') === undefined)) {
                            $(elm).attr('required', 'required');
                            if(!$(label).find('span.Form-requiredAsterisk').length){
                                $(label).prepend('<span class="Form-requiredAsterisk">*</span>');
                            }
                        } else if (!isRequired) {
                            elm.removeAttr('required');
                            if (!attrs.awrequiredAlwaysShowAsterisk) {
                                $(label).find('span.Form-requiredAsterisk').remove();
                            }
                        }
                        if (isRequired && (viewValue === undefined || viewValue === null || viewValue === '')) {
                            validity = false;
                        }
                        ctrl.$setValidity('required', validity);
                    }

                    scope.$watchGroup([attrs.awRequiredWhen, $(elm).attr('name')], function() {
                        // watch for the aw-required-when expression to change value
                        updateRequired();
                    });

                    if (attrs.awrequiredInit !== undefined && attrs.awrequiredInit !== null) {
                        // We already set a watcher on the attribute above so no need to call updateRequired() in here
                        scope[attrs.awRequiredWhen] = attrs.awrequiredInit;
                    }
                }
            };
        }
    };
})

// awPlaceholder: Dynamic placeholder set to a scope variable you want watched.
//                Value will be place in field placeholder attribute.
.directive('awPlaceholder', [function() {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs) {
            $(elm).attr('placeholder', scope[attrs.awPlaceholder]);
            scope.$watch(attrs.awPlaceholder, function(newVal) {
                $(elm).attr('placeholder', newVal);
            });
        }
    };
}])

// lookup   Validate lookup value against API
.directive('awlookup', ['Rest', 'GetBasePath', '$q', '$state', function(Rest, GetBasePath, $q, $state) {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, fieldCtrl) {
            let query,
                basePath,
                defer = $q.defer(),
                autopopulateLookup,
                modelKey = attrs.ngModel,
                modelName = attrs.source,
                watcher = attrs.awRequiredWhen || undefined,
                watchBasePath,
                awLookupWhen = attrs.awLookupWhen;

            if (attrs.autopopulatelookup !== undefined) {
               autopopulateLookup = JSON.parse(attrs.autopopulatelookup);
            } else {
               autopopulateLookup = true;
            }

            // The following block of code is for instances where the
            // lookup field is reused by varying sub-forms. Example: The groups
            // form will change it's credential lookup based on the
            // source type. The basepath the lookup should utilize is dynamic
            // in this case. You'd configure the "watchBasePath" key on the
            // field's configuration in the form configuration field.
            if (attrs.watchbasepath !== undefined) {
                watchBasePath = attrs.watchbasepath;
                scope.$watch(watchBasePath, (newValue) => {
                    if(newValue !== undefined && fieldIsAutopopulatable()){
                        _doAutoPopulate();
                    }
                });
            }

            function _doAutoPopulate() {
                let query = '?role_level=use_role';

                if (attrs.watchbasepath !== undefined && scope[attrs.watchbasepath] !== undefined) {
                    basePath = scope[attrs.watchbasepath];
                    if (attrs.watchbasepath !== "projectBasePath") {
                        query = '&role_level=use_role';
                    } else {
                        query = '';
                    }
                }
                else {
                    basePath = GetBasePath(elm.attr('data-basePath')) || elm.attr('data-basePath');
                    let switchType = attrs.awlookuptype ? attrs.awlookuptype : modelName;

                    switch(switchType) {
                        case 'credential':
                            query = '?credential_type__kind=ssh&role_level=use_role';
                            break;
                        case 'scm_credential':
                            query = '?credential_type__kind=scm&role_level=use_role';
                            break;
                        case 'network_credential':
                            query = '?credential_type__kind=net&role_level=use_role';
                            break;
                        case 'insights_credential':
                            query = '?credential_type__kind=insights&role_level=use_role';
                            break;
                        case 'organization':
                            query = '?role_level=admin_role';
                            break;
                        case 'inventory_script':
                            query = '?role_level=admin_role&organization=' + scope.$resolve.inventoryData.summary_fields.organization.id;
                            break;
                    }

                }

                Rest.setUrl(`${basePath}` + query);
                Rest.get()
                .then(({data}) => {
                    if (data.count === 1) {
                        scope[modelKey] = data.results[0].name;
                        scope[modelName] = data.results[0].id;
                    }
                });
            }

            if (fieldIsAutopopulatable()) {
                _doAutoPopulate();
            }

            // This checks to see if the field meets the criteria to
            // autopopulate:
            // Population rules:
            // - add form only
            // - lookup is required
            // - lookup is not promptable
            // - user must only have access to 1 item the lookup is for
            function fieldIsAutopopulatable() {
                if (autopopulateLookup === false) {
                    return false;
                }
                if (scope.mode === "add") {
                    if(watcher){
                        scope.$watch(watcher, () => {
                            if(Boolean(scope.$eval(watcher)) === true){

                                // if we get here then the field is required
                                // by way of awRequiredWhen
                                // and is a candidate for autopopulation

                                _doAutoPopulate();
                            }
                        });
                    }
                    else if (attrs.required === true) {
                        return true;
                    }
                    else {
                        return false;
                    }
                }
                else {
                    return false;
                }
            }

            // query the API to see if field value corresponds to a valid resource
            // .ng-pending will be applied to the directive element while the request is outstanding
            // form.$pending will contain object reference to any ngModelControllers with outstanding requests
            fieldCtrl.$asyncValidators.validResource = function(modelValue, viewValue) {

                if(awLookupWhen === undefined || (awLookupWhen !== undefined && Boolean(scope.$eval(awLookupWhen)) === true)) {
                    applyValidationStrategy(viewValue, fieldCtrl);
                }
                else {
                    defer.resolve();
                }

                return defer.promise;
            };

            function applyValidationStrategy(viewValue, ctrl) {

                // use supplied data attributes to build an endpoint, query, resolve outstanding promise
                function applyValidation(viewValue) {
                    basePath = GetBasePath(elm.attr('data-basePath')) || elm.attr('data-basePath');
                    query = elm.attr('data-query');
                    query = query.replace(/\:value/, encodeURIComponent(viewValue));

                    let base = attrs.awlookuptype ? attrs.awlookuptype : ctrl.$name.split('_name')[0];
                    if (attrs.watchbasepath !== undefined && scope[attrs.watchbasepath] !== undefined) {
                        basePath = scope[attrs.watchbasepath];
                        query += '&role_level=use_role';
                        query = query.replace('?', '&');
                    }
                    else {
                        switch(base) {
                            case 'credential':
                                query += '&credential_type__namespace=ssh&role_level=use_role';
                                break;
                            case 'scm_credential':
                                query += '&credential_type__namespace=scm&role_level=use_role';
                                break;
                            case 'network_credential':
                                query += '&credential_type__namespace=net&role_level=use_role';
                                break;
                            case 'cloud_credential':
                                query += '&cloud=true&role_level=use_role';
                                break;
                            case 'organization':
                                if ($state.current.name.includes('inventories')) {
                                    query += '&role_level=inventory_admin_role';
                                } else if ($state.current.name.includes('templates.editWorkflowJobTemplate')) {
                                    query += '&role_level=workflow_admin_role';
                                } else if ($state.current.name.includes('projects')) {
                                    query += '&role_level=project_admin_role';
                                } else if ($state.current.name.includes('notifications')) {
                                    query += '&role_level=notification_admin_role';
                                } else {
                                    query += '&role_level=admin_role';
                                }
                                break;
                            case 'inventory_script':
                                query += '&role_level=admin_role&organization=' + scope.$resolve.inventoryData.summary_fields.organization.id;
                                break;
                            default:
                                query += '&role_level=use_role';
                        }
                    }

                    Rest.setUrl(`${basePath}${query}`);
                    // https://github.com/ansible/ansible-tower/issues/3549
                    // capturing both success/failure conditions in .then() promise
                    // when #3549 is resolved, this will need to be partitioned into success/error or then/catch blocks
                    return Rest.get()
                        .then((res) => {
                            if (res.data.results.length > 0) {
                                scope[elm.attr('data-source')] = res.data.results[0].id;
                                return setValidity(ctrl, true);
                            } else {
                                scope[elm.attr('data-source')] = null;
                                return setValidity(ctrl, false);
                            }
                        });
                }

                function setValidity(ctrl, validity){
                    var isRequired;
                    if (attrs.required) {
                        isRequired = true;
                    } else {
                        isRequired = false;
                    }
                    if (attrs.awRequiredWhen) {
                      if (attrs.awRequiredWhen.charAt(0) === "!") {
                        isRequired = !scope[attrs.awRequiredWhen.slice(1, attrs.awRequiredWhen.length)];
                      } else {
                        isRequired = scope[attrs.awRequiredWhen];
                      }
                    }
                    if (!isRequired && (viewValue === undefined || viewValue === undefined || viewValue === "")) {
                        validity = true;
                    }
                    ctrl.$setValidity('awlookup', validity);
                    return defer.resolve(validity);
                }

                // Three common cases for clarity:

                // 1) Field is not required & pristine. Pass validation & skip async $pending state
                // 2) Field is required. Always validate & use async $pending state
                // 3) Field is not required, but is not $pristine. Always validate & use async $pending state

                // case 1
                if (!ctrl.$validators.required && ctrl.$pristine) {
                    return setValidity(ctrl, true);
                }
                // case 2 & 3
                else {
                    return applyValidation(viewValue);
                }
            }
        }
    };
}])

//
// awValidUrl
//
.directive('awValidUrl', [function() {
    return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                var validity = true,
                    rgx, rgx2;
                if (viewValue !== '') {
                    ctrl.$setValidity('required', true);
                    rgx = /^(https|http|ssh)\:\/\//;
                    rgx2 = /\@/g;
                    if (!rgx.test(viewValue) || rgx2.test(viewValue)) {
                        validity = false;
                    }
                }
                ctrl.$setValidity('awvalidurl', validity);

                return viewValue;
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
.directive('awToolTip', ['$transitions', function($transitions) {
    return {
        link: function(scope, element, attrs) {
            var delay = { show: 200, hide: 0 },
                placement,
                container,
                stateChangeWatcher;
            if (attrs.awTipPlacement) {
                placement = attrs.awTipPlacement;
            } else {
                placement = (attrs.placement !== undefined && attrs.placement !== null) ? attrs.placement : 'left';
            }

            container = attrs.container ? attrs.container : 'body';

            var template;

            let tooltipInnerClass = (attrs.tooltipInnerClass || attrs.tooltipinnerclass) ? (attrs.tooltipInnerClass || attrs.tooltipinnerclass) : '';
            let tooltipOuterClass = attrs.tooltipOuterClass ? attrs.tooltipOuterClass : '';

            template = '<div class="tooltip Tooltip ' + tooltipOuterClass + '" role="tooltip"><div class="tooltip-arrow Tooltip-arrow arrow"></div><div class="tooltip-inner Tooltip-inner ' + tooltipInnerClass + '"></div></div>';

            // This block helps clean up tooltips that may get orphaned by a click event
            $(element).on('mouseenter', function(event) {

                var elem = $(event.target).parent();
                if (elem[0].nodeName === "SOURCE-SUMMARY-POPOVER") {
                    $('.popover').popover('hide');
                }

                if (stateChangeWatcher) {
                    // Un-bind - we don't want a bunch of listeners firing
                    stateChangeWatcher();
                }

                stateChangeWatcher = $transitions.onStart({}, function() {
                    // Go ahead and force the tooltip setTimeout to expire (if it hasn't already fired)
                    $(element).tooltip('hide');
                    // Clean up any existing tooltips including this one
                    $('.tooltip').each(function() {
                        $(this).remove();
                    });
                });
            });

            $(element).on('hidden.bs.tooltip', function() {
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
                container: container,
                trigger: 'hover',
                template: template,
                boundary: 'window'
            });

            if (attrs.tipWatch) {
                // Add dataTipWatch: 'variable_name'
                scope.$watch(attrs.tipWatch, function(newVal) {
                    // Where did fixTitle come from?:
                    //   http://stackoverflow.com/questions/9501921/change-twitter-bootstrap-tooltip-content-on-click
                    $(element).tooltip('hide').attr('data-original-title', newVal).tooltip('_fixTitle');
                });
            }
        }
    };
}])

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
            title = (attrs.overTitle) ? attrs.overTitle : (attrs.popoverTitle) ? attrs.popoverTitle : 'Help',
            container = (attrs.container !== undefined) ? attrs.container : false,
            trigger = (attrs.trigger !== undefined) ? attrs.trigger : 'manual',
            template = '<div class="popover" role="tooltip"><div class="arrow"></div><h3 class="popover-header"></h3><div class="popover-body"></div></div>',
            id_to_close = "";

        if (element[0].id) {
            template = '<div id="' + element[0].id + '_popover_container" class="popover" role="tooltip"><div class="arrow"></div><span id="' + element[0].id + '_popover_container"><h3 id="' + element[0].id + '_popover_title" class="popover-header" translate></h3><div id="' + element[0].id + '_popover_content" class="popover-body" translate></div></span></div>';
        }

        scope.triggerPopover = function(e) {
            showPopover(e);
        };

        if (attrs.awPopOverWatch) {
            $(element).popover({
                placement: placement,
                delay: 0,
                title: title,
                content: function() {
                    return _.get(scope, attrs.awPopOverWatch);
                },
                trigger: trigger,
                html: true,
                container: container,
                template: template
            });
        } else {
            $(element).popover({
                placement: placement,
                delay: 0,
                title: title,
                content: attrs.awPopOver,
                trigger: trigger,
                html: true,
                container: container,
                template: template
            });
        }
        $(element).attr('tabindex', -1);

        $(element).one('click', showPopover);

        function bindPopoverDismiss() {
            $('body').one('click.popover' + id_to_close, function(e) {
                if ($(e.target).parents(id_to_close).length === 0) {
                    // case: you clicked to open the popover and then you
                    //  clicked outside of it...hide it.
                    $(element).popover('hide');
                } else {
                    // case: you clicked to open the popover and then you
                    // clicked inside the popover
                    bindPopoverDismiss();
                }
            });
        }

        $(element).on('shown.bs.popover', function() {
            bindPopoverDismiss();
            $(document).on('keydown.popover', dismissOnEsc);
        });

        $(element).on('hidden.bs.popover', function() {
            $(element).off('click', dismissPopover);
            $(element).off('click', showPopover);
            $('body').off('click.popover.' + id_to_close);
            $(element).one('click', showPopover);
            $(document).off('keydown.popover', dismissOnEsc);
        });

        function showPopover(e) {
            e.stopPropagation();

            var self = $(element);

            // remove tool-tip
            try {
                element.tooltip('hide');
            } catch (ex) {
                // ignore
            }

            // this is called on the help-link (over and over again)
            $('.help-link, .help-link-white').each(function() {
                if (self.attr('id') !== $(this).attr('id')) {
                    try {
                        // not sure what this does different than the method above
                        $(this).popover('hide');
                    } catch (e) {
                        // ignore
                    }
                }
            });

            $('.popover').each(function() {
                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                $(this).remove();
            });
            $('.tooltip').each(function() {
                // close any lingering tool tips
                $(this).hide();
            });

            // set id_to_close of the actual open element
            id_to_close = "#" + $(element).attr('id') + "_popover_container";

            // $(element).one('click', dismissPopover);

            $(element).popover('toggle');

            $('.popover').each(function() {
                $compile($(this))(scope); //make nested directives work!
            });
        }

        function dismissPopover(e) {
            e.stopPropagation();
            $(element).popover('hide');
        }

        function dismissOnEsc(e) {
            if (e.keyCode === 27) {
                $(element).popover('hide');
                $('.popover').each(function() {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    // $(this).remove();
                });
            }
        }

    };
}])

//
// Enable jqueryui slider widget on a numeric input field
//
// <input type="number" aw-slider name="myfield" min="0" max="100" />
//
.directive('awSlider', [function() {
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
                slide: function(e, u) {
                    ctrl.$setViewValue(u.value);
                    ctrl.$setValidity('required', true);
                    ctrl.$setValidity('min', true);
                    ctrl.$setValidity('max', true);
                    ctrl.$dirty = true;
                    ctrl.$render();
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                }
            });

            $('#' + name + '-number').change(function() {
                $('#' + name + '-slider').slider('value', parseInt($(this).val(), 10));
            });

        }
    };
}])

//
// Enable jqueryui spinner widget on a numeric input field
//
// <input type="number" aw-spinner name="myfield" min="0" max="100" />
//
.directive('awSpinner', [function() {
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
                icons: {
                    down: "Form-numberInputButton fa fa-angle-down",
                    up: "Form-numberInputButton fa fa-angle-up"
                },
                spin: function(e, u) {
                    if (e.originalEvent && e.originalEvent.type === 'mousewheel') {
                        e.preventDefault();
                    } else {
                        ctrl.$setViewValue(u.value);
                        ctrl.$setValidity('required', true);
                        ctrl.$setValidity('min', true);
                        ctrl.$setValidity('max', true);
                        ctrl.$dirty = true;
                        ctrl.$render();
                        if (scope.job_template_form) {
                            // need a way to find the parent form and mark it dirty
                            scope.job_template_form.$dirty = true;
                        }
                        if (!scope.$$phase) {
                            scope.$digest();
                        }
                    }
                }
            };

            // hack to get ngDisabled to work
            if (attrs.ngDisabled) {
                scope.$watch(attrs.ngDisabled, function(val) {
                    opts.disabled = (val === true) ? true : false;
                    $(elm).spinner(opts);
                });
            }

            if (disabled) {
                opts.disabled = true;
            }
            $(elm).spinner(opts);
            $('.ui-icon').text('');
            $(".ui-icon").removeClass('ui-icon ui-icon-triangle-1-n ui-icon-triangle-1-s');
            $(elm).on("click", function() {
                $(elm).select();
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
.directive('awDraggable', [function() {
    return function(scope, element, attrs) {

        if (attrs.awDraggable === "true") {
            var containment = attrs.containment; //provide dataContainment:"#id"
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

// Toggle switch inspired by http://www.bootply.com/92189
.directive('awToggleButton', [function() {
    return function(scope, element) {
        $(element).click(function() {
            var next, choice;
            $(this).find('.btn').toggleClass('active');
            if ($(this).find('.btn-primary').size() > 0) {
                $(this).find('.btn').toggleClass('btn-primary');
            }
            if ($(this).find('.btn-danger').size() > 0) {
                $(this).find('.btn').toggleClass('btn-danger');
            }
            if ($(this).find('.btn-success').size() > 0) {
                $(this).find('.btn').toggleClass('btn-success');
            }
            if ($(this).find('.btn-info').size() > 0) {
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
                    ctrl.$setValidity('required', true);
                    ctrl.$dirty = true;
                    if (!scope.$$phase) {
                        scope.$digest();
                    }
                };
                reader.onerror = function() {
                    Alert('Error', 'There was an error reading the selected file.');
                };
                if (files[0].size < 10000) {
                    reader.readAsText(files[0]);
                } else {
                    Alert('Error', 'There was an error reading the selected file.');
                }
            });
        }
    };
}])

.directive('awPasswordToggle', [function() {
    return {
        restrict: 'A',
        link: function(scope, element) {
            $(element).click(function() {
                var buttonInnerHTML = $(element).html();
                if (buttonInnerHTML.indexOf("Show") > -1) {
                    $(element).html("Hide");
                    $(element).closest('.input-group').find('input').first().attr("type", "text");
                } else {
                    $(element).html("Show");
                    $(element).closest('.input-group').find('input').first().attr("type", "password");
                }
            });
        }
    };
}])

.directive('awEnterKey', [function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            element.bind("keydown keypress", function(event) {
                var keyCode = event.which || event.keyCode;
                if (keyCode === 13) {
                    scope.$apply(function() {
                        scope.$eval(attrs.awEnterKey);
                    });
                    event.preventDefault();
                }
            });
        }
    };
}])

.directive('awTruncateBreadcrumb', ['BreadCrumbService', function(BreadCrumbService) {
    return {
        restrict: 'A',
        scope: {
            breadcrumbStep: '='
        },
        link: function(scope) {
            scope.$watch('breadcrumbStep.ncyBreadcrumbLabel', function(){
                BreadCrumbService.truncateCrumbs();
            });
        }
    };
}])

.directive('awRequireMultiple', ['Empty', function(Empty) {
    return {
        require: 'ngModel',
        link: function postLink(scope, element, attrs, ngModel) {
            // Watch for changes to the required attribute
            attrs.$observe('required', function() {
                ngModel.$validate();
            });

            ngModel.$validators.multipleSelect = function (modelValue) {
                if(attrs.required) {
                    if(angular.isArray(modelValue)) {
                        // Checks to make sure at least one value in the array
                        return _.some(modelValue, function(arrayVal) {
                            return !Empty(arrayVal);
                        });
                    } else {
                        return !Empty(modelValue);
                    }
                } else {
                    return true;
                }
            };
        }
    };
}]);
