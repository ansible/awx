/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


/**
 *  @ngdoc function
 *  @name shared.function:Utilities
 *  @description
 *  Utility functions
 *
 */

/* jshint devel:true */



export default
angular.module('Utilities', ['RestServices', 'Utilities'])

/**
 * @ngdoc method
 * @name shared.function:Utilities#Empty
 * @methodOf shared.function:Utilities
 * @description Empty()
 *
 * Test if a value is 'empty'. Returns true if val is null | '' | undefined.
 * Only works on non-Ojbect types.
 *
 */
.factory('Empty', [
    function() {
        return function(val) {
            return (val === null || val === undefined || val === '') ? true : false;
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#ToggleClass
 * @methodOf shared.function:Utilities
 * @description
 */
.factory('ToggleClass', function() {
    return function(selector, cssClass) {
        // Toggles the existance of a css class on a given element
        if ($(selector) && $(selector).hasClass(cssClass)) {
            $(selector).removeClass(cssClass);
        } else if ($(selector)) {
            $(selector).addClass(cssClass);
        }
    };
})


/**
 * @ngdoc method
 * @name shared.function:Utilities#Alert
 * @methodOf shared.function:Utilities
 * @description Pass in the header and message you want displayed on TB modal dialog found in index.html.
 * Assumes an #id of 'alert-modal'. Pass in an optional TB alert class (i.e. alert-danger, alert-success,
 * alert-info...). Pass an optional function(){}, if you want a specific action to occur when user
 * clicks 'OK' button. Set secondAlert to true, when a second dialog is needed.
 */
.factory('Alert', ['$rootScope', '$filter', function($rootScope, $filter) {
    return function(hdr, msg, cls, action, secondAlert, disableButtons, backdrop, customStyle) {
        var scope = $rootScope.$new(),
            alertClass, local_backdrop;
        if (customStyle !== true) {
            msg = $filter('sanitize')(msg);
        }
        if (secondAlert) {

            $('#alertHeader2').html(hdr);
            $('#alert2-modal-msg').html(msg);

            alertClass = (cls) ? cls : 'alert-danger'; //default alert class is alert-danger
            local_backdrop = (backdrop === undefined || backdrop === null) ? "static" : backdrop;

            $('#alert2-modal-msg').attr({ "class": "alert " + alertClass });
            $('#alert-modal2').modal({
                show: true,
                keyboard: true,
                backdrop: local_backdrop
            });
            scope.disableButtons2 = (disableButtons) ? true : false;

            $('#alert-modal2').on('hidden.bs.modal', function() {
                $(document).unbind('keydown');
                if (action) {
                    action();
                }
                $('#alert-modal2').off();
            });
            $('#alert-modal2').on('shown.bs.modal', function() {
                $('#alert2_ok_btn').focus();
            });
            $(document).bind('keydown', function(e) {
                if (e.keyCode === 27 || e.keyCode === 13) {
                    e.preventDefault();
                    $('#alert-modal2').modal('hide');
                }
            });
        } else {

            $('#alertHeader').html(hdr);
            $('#alert-modal-msg').html(msg);
            alertClass = (cls) ? cls : 'alert-danger'; //default alert class is alert-danger
            local_backdrop = (backdrop === undefined || backdrop === null) ? "static" : backdrop;

            $('#alert-modal-msg').attr({ "class": "alert " + alertClass });
            $('#alert-modal').modal({
                show: true,
                keyboard: true,
                backdrop: local_backdrop
            });

            $('#alert-modal').on('hidden.bs.modal', function() {
                $(document).unbind('keydown');
                if (action) {
                    action();
                }
                $('.modal-backdrop').remove();
                $('#alert-modal').off();
            });
            $('#alert-modal').on('shown.bs.modal', function() {
                $('#alert_ok_btn').focus();
            });
            $(document).bind('keydown', function(e) {
                if (e.keyCode === 27 || e.keyCode === 13) {
                    e.preventDefault();
                    $('#alert-modal').modal('hide');
                }
            });

            scope.disableButtons = (disableButtons) ? true : false;
        }
    };
}])

/**
 * @ngdoc method
 * @name shared.function:Utilities#ProcessErrors
 * @methodOf shared.function:Utilities
 * @description For handling errors that are returned from the API
 */
.factory('ProcessErrors', ['$rootScope', '$cookies', '$log', '$location', 'Alert', 'Wait',
    function($rootScope, $cookies, $log, $location, Alert, Wait) {
        return function(scope, data, status, form, defaultMsg) {
            var field, fieldErrors, msg, keys;
            Wait('stop');
            $log.debug('Debug status: ' + status);
            $log.debug('Debug data: ');
            $log.debug(data);
            if (defaultMsg.msg) {
                $log.debug('Debug: ' + defaultMsg.msg);
            }
            if (status === 403) {
                if (data && data.detail) {
                    msg = data.detail;
                } else {
                    msg = 'The API responded with a 403 Access Denied error. Please contact your system administrator.';
                }
                Alert(defaultMsg.hdr, msg);
            } else if (status === 409) {
                Alert('Conflict', data.conflict || "Resource currently in use.");
            } else if (status === 410) {
                Alert('Deleted Object', 'The requested object was previously deleted and can no longer be accessed.');
            } else if ((status === 'Session is expired') || (status === 401)) {
                if ($rootScope.sessionTimer) {
                    $rootScope.sessionTimer.expireSession('idle');
                }
                $location.url('/login');
            } else if (data && data.non_field_errors) {
                Alert('Error!', data.non_field_errors);
            } else if (data && data.detail) {
                Alert(defaultMsg.hdr, defaultMsg.msg + ' ' + data.detail);
            } else if (data && data.__all__) {
                if (typeof data.__all__ === 'object' && Array.isArray(data.__all__)) {
                    Alert('Error!', data.__all__[0]);
                } else {
                    Alert('Error!', data.__all__);
                }
            } else if (form) { //if no error code is detected it begins to loop through to see where the api threw an error
                fieldErrors = false;

                const addApiErrors = (field, fld) => {
                    if (data[fld] && field.tab) {
                        // If the form is part of a tab group, activate the tab
                        $('#' + form.name + "_tabs a[href=\"#" + field.tab + '"]').tab('show');
                    }
                    if (field.realName) {
                        if (field.realName) {
                            scope[fld + '_api_error'] = data[field.realName][0];
                            //scope[form.name + '_form'][form.fields[field].realName].$setValidity('apiError', false);
                            $('[name="' + field.realName + '"]').addClass('ng-invalid');
                            $('html, body').animate({scrollTop: $('[name="' + field.realName + '"]').offset().top}, 0);
                            fieldErrors = true;
                        }
                    }
                    if (field.sourceModel) {
                        if (data[fld]) {
                            scope[field.sourceModel + '_' + field.sourceField + '_api_error'] =
                                data[fld][0];
                            //scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField].$setValidity('apiError', false);
                            $('[name="' + field.sourceModel + '_' + field.sourceField + '"]').addClass('ng-invalid');
                            $('[name="' + field.sourceModel + '_' + field.sourceField + '"]').ScrollTo({ "onlyIfOutside": true, "offsetTop": 100 });
                            fieldErrors = true;
                        }
                    } else {
                        if (data[fld]) {
                            if (data[fld].message) {
                                scope[fld + '_api_error'] = data[fld].message;
                            } else {
                                scope[fld + '_api_error'] = data[fld][0];
                            }
                            $('[name="' + fld + '"]').addClass('ng-invalid');
                            $('label[for="' + fld + '"] span').addClass('error-color');
                            $('html, body').animate({scrollTop: $('[name="' + fld + '"]').offset().top}, 0);
                            fieldErrors = true;
                            if(field.codeMirror){
                                $(`#cm-${fld}-container .CodeMirror`).addClass('error-border');
                            }
                        }
                    }
                };

                for (field in form.fields) {
                    if (form.fields[field].type === "checkbox_group") {
                        form.fields[field].fields.forEach(fld => {
                            addApiErrors(fld, fld.name);
                        });
                    } else {
                        addApiErrors(form.fields[field], field);
                    }
                }
                if (!fieldErrors && defaultMsg) {
                    Alert(defaultMsg.hdr, defaultMsg.msg);
                }
            } else if (typeof data === 'object' && data !== null) {
                if (Object.keys(data).length > 0) {
                    keys = Object.keys(data);
                    msg = "";
                    _.forOwn(data, function(value, key) {
                        if (Array.isArray(data[key])) {
                            msg += `${key.toUpperCase()}: ${data[key][0]}`;
                        } else {
                            msg += `${key.toUpperCase()}: ${value} `;
                        }
                    });
                    Alert(defaultMsg.hdr, msg);
                } else {
                    Alert(defaultMsg.hdr, defaultMsg.msg);
                }
            } else {
                Alert(defaultMsg.hdr, defaultMsg.msg);
            }
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#HelpDialog
 * @methodOf shared.function:Utilities
 * @description Display a help dialog
 *
 * HelpDialog({ defn: <HelpDefinition> })
 * discuss difference b/t this and other modal windows/dialogs
 */
.factory('HelpDialog', ['$rootScope', '$compile', '$location', 'Store',
    function($rootScope, $compile, $location, Store) {
        return function(params) {

            var defn = params.defn,
                current_step = params.step,
                autoShow = params.autoShow || false,
                scope = (params.scope) ? params.scope : $rootScope.$new();

            function setButtonMargin() {
                var width = ($('.ui-dialog[aria-describedby="help-modal-dialog"] .ui-dialog-buttonpane').innerWidth() / 2) - $('#help-next-button').outerWidth() - 93;
                $('#help-next-button').css({ 'margin-right': width + 'px' });
            }

            function showHelp(step) {

                var e, btns, ww, width, height, isOpen = false;
                current_step = step;

                function buildHtml(step) {
                    var html = '';
                    html += "<h4>" + step.intro + "</h4>\n";
                    if (step.img) {
                        html += "<div class=\"img-container\">\n";
                        html += "<img src=\"" + $basePath + "assets/help/" + step.img.src + "\" ";
                        html += (step.img.maxWidth) ? "style=\"max-width:" + step.img.maxWidth + "px\" " : "";
                        html += ">";
                        html += "</div>\n";
                    }
                    if (step.icon) {
                        html += "<div class=\"icon-container\"";
                        html += (step.icon.containerHeight) ? "style=\"height:" + step.icon.containerHeight + "px;\">\n" : "";
                        html += "<i class=\"" + step.icon['class'] + "\" ";
                        html += (step.icon.style) ? "style=\"" + step.icon.style + "\" " : "";
                        html += "></i>\n";
                        html += "</div>\n";
                    }
                    html += "<div class=\"help-box\">" + step.box + "</div>";
                    html += (autoShow && step.autoOffNotice) ? "<div class=\"help-auto-off\"><label><input type=\"checkbox\" " +
                        "name=\"auto-off-checkbox\" id=\"auto-off-checkbox\"> Do not show this message in the future</label></div>\n" : "";
                    return html;
                }

                width = (defn.story.width) ? defn.story.width : 510;
                height = (defn.story.height) ? defn.story.height : 600;

                // Limit modal width to width of viewport
                ww = $(document).width();
                width = (width > ww) ? ww : width;

                try {
                    isOpen = $('#help-modal-dialog').dialog('isOpen');
                } catch (err) {
                    // ignore
                }

                e = angular.element(document.getElementById('help-modal-dialog'));
                e.empty().html(buildHtml(defn.story.steps[current_step]));
                setTimeout(function() { scope.$apply(function() { $compile(e)(scope); }); });

                if (!isOpen) {
                    // Define buttons based on story length
                    btns = [];
                    if (defn.story.steps.length > 1) {
                        btns.push({
                            text: "Prev",
                            click: function() {
                                if (current_step - 1 === 0) {
                                    $('#help-prev-button').prop('disabled', true);
                                }
                                if (current_step - 1 < defn.story.steps.length - 1) {
                                    $('#help-next-button').prop('disabled', false);
                                }
                                showHelp(current_step - 1);
                            },
                            disabled: true
                        });
                        btns.push({
                            text: "Next",
                            click: function() {
                                if (current_step + 1 > 0) {
                                    $('#help-prev-button').prop('disabled', false);
                                }
                                if (current_step + 1 >= defn.story.steps.length - 1) {
                                    $('#help-next-button').prop('disabled', true);
                                }
                                showHelp(current_step + 1);
                            }
                        });
                    }
                    btns.push({
                        text: "Close",
                        click: function() {
                            $('#help-modal-dialog').dialog('close');
                        }
                    });

                    $('.overlay').css({
                        width: $(document).width(),
                        height: $(document).height()
                    }).fadeIn();

                    // Show the dialog
                    $('#help-modal-dialog').dialog({
                        position: {
                            my: "center top",
                            at: "center top+150",
                            of: 'body'
                        },
                        title: defn.story.hdr,
                        width: width,
                        height: height,
                        buttons: btns,
                        closeOnEscape: true,
                        show: 500,
                        hide: 500,
                        resizable: false,
                        close: function() {
                            $('.overlay').hide();
                            $('#help-modal-dialog').empty();
                        }
                    });

                    // Make the buttons look like TB and add FA icons
                    $('.ui-dialog-buttonset button').each(function() {
                        var c, h, i, l;
                        l = $(this).text();
                        if (l === 'Close') {
                            h = "fa-times";
                            c = "btn btn-default";
                            i = "help-close-button";
                            $(this).attr({
                                'class': c,
                                'id': i
                            }).html("<i class=\"fa " + h + "\"></i> Close");
                        } else if (l === 'Prev') {
                            h = "fa-chevron-left";
                            c = "btn btn-primary";
                            i = "help-prev-button";
                            $(this).attr({
                                'class': c,
                                'id': i
                            }).html("<i class=\"fa " + h + "\"></i> Prev");
                        } else {
                            h = "fa-chevron-right";
                            c = "btn btn-primary";
                            i = "help-next-button";
                            $(this).attr({
                                'class': c,
                                'id': i
                            }).html("Next <i class=\"fa " + h + "\"></i>").css({
                                'margin-right': '20px'
                            });
                        }
                    });

                    $('.ui-dialog[aria-describedby="help-modal-dialog"]').find('.ui-dialog-titlebar button')
                        .empty().attr({
                            'class': 'close'
                        }).text('x');

                    // If user clicks the checkbox, update local storage
                    $('#auto-off-checkbox').click(function() {
                        if ($('input[name="auto-off-checkbox"]:checked').length) {
                            Store('inventoryAutoHelp', 'off');
                        } else {
                            Store('inventoryAutoHelp', 'on');
                        }
                    });

                    setButtonMargin();
                }
            }

            showHelp(0);
        };
    }
])


/**
 * @ngdoc method
 * @name shared.function:Utilities#ReturnToCaller
 * @methodOf shared.function:Utilities
 * @description
 * Split the current path by '/' and use the array elements from 0 up to and
 * including idx as the new path.  If no idx value supplied, use 0 to length - 1.
 *
 */
.factory('ReturnToCaller', ['$location', 'Empty',
    function($location, Empty) {
        return function(idx) {
            var paths = $location.path().replace(/^\//, '').split('/'),
                newpath = '',
                i;
            idx = (Empty(idx)) ? paths.length - 1 : idx + 1;
            for (i = 0; i < idx; i++) {
                newpath += '/' + paths[i];
            }
            $location.path(newpath);
        };
    }
])


/**
 * @ngdoc method
 * @name shared.function:Utilities#FormatDate
 * @methodOf shared.function:Utilities
 * @description
 * Wrapper for data filter- an attempt to insure all dates display in
 * the same format. Pass in date object or string. See: http://docs.angularjs.org/api/ng.filter:date
 */
.factory('FormatDate', ['$filter',
    function($filter) {
        return function(dt) {
            return $filter('longDate')(dt);
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#Wait
 * @methodOf shared.function:Utilities
 * @description
 * Display a spinning icon in the center of the screen to freeze the
 * UI while waiting on async things to complete (i.e. API calls).
 * Wait('start' | 'stop');
 *
 */
.factory('Wait', ['$rootScope',
    function($rootScope) {

        return function(directive) {
            var docw, doch, spinnyw, spinnyh;
            if (directive === 'start' && !$rootScope.waiting) {
                $rootScope.waiting = true;
                docw = $(window).width();
                doch = $(window).height();
                spinnyw = $('.spinny').width();
                spinnyh = $('.spinny').height();
                $('.overlay').css({
                    width: $(document).width(),
                    height: $(document).height()
                }).fadeIn();
                $('.spinny').css({
                    bottom: 15,
                    right: 15
                }).fadeIn(400);
            } else if (directive === 'stop' && $rootScope.waiting) {
                $('.spinny, .overlay').fadeOut(400, function() {
                    $rootScope.waiting = false;
                });
            }
        };
    }
])

.factory('HideElement', [
    function() {
        return function(selector, action) {
            // Fade-in a cloack or vail or a specific element
            var target = $(selector),
                width = target.css('width'),
                height = target.css('height'),
                position = target.position(),
                parent = target.parent(),
                borderRadius = target.css('border-radius'),
                backgroundColor = target.css('background-color'),
                margin = target.css('margin'),
                padding = target.css('padding');

            parent.append("<div id=\"curtain-div\" style=\"" +
                "position: absolute;" +
                "top: " + position.top + "px; " +
                "left: " + position.left + "px; " +
                "z-index: 1000; " +
                "width: " + width + "; " +
                "height: " + height + "; " +
                "background-color: " + backgroundColor + "; " +
                "margin: " + margin + "; " +
                "padding: " + padding + "; " +
                "border-radius: " + borderRadius + "; " +
                "opacity: .75; " +
                "display: none; " +
                "\"></div>");
            $('#curtain-div').show(0, action);
        };
    }
])

.factory('ShowElement', [
    function() {
        return function() {
            // And Fade-out the cloack revealing the element
            $('#curtain-div').fadeOut(500, function() {
                $(this).remove();
            });
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#CreateSelect2
 * @methodOf shared.function:Utilities
 * @description Make a regular select drop down a select2 dropdown
 *  To make a ``<select>`` field a select2 select 2, create the field in the
 *  form definition with the multiSelect flag set to true. In the controller
 *  of the page in question, call the CreateSelect2 factory with the element
 *  id (be sure to include the appropriate jquery identifier in the parameter)
 *  or any options that should be pre-selected in the select2 field.
 *  The array of options should be formatted as
 * ```
 * [
 *  {
 *     id: 'id' ,
 *     text: 'text'
 *  },
 *  {
 *     id: 'id' ,
 *     text: 'text'
 *  }
 * ]
 * ```
 */
.factory('CreateSelect2', ['$filter', '$q',
        function($filter, $q) {
            return function(params) {

                var element = params.element,
                    options = params.opts,
                    multiple = (params.multiple !== undefined) ? params.multiple : true,
                    placeholder = params.placeholder,
                    customDropdownAdapter = (params.customDropdownAdapter !== undefined) ? params.customDropdownAdapter : true,
                    addNew = params.addNew,
                    scope = params.scope,
                    selectOptions = params.options,
                    model = params.model,
                    original_options,
                    minimumResultsForSearch = params.minimumResultsForSearch ? params.minimumResultsForSearch : Infinity,
                    defer = $q.defer();

                    if (scope && selectOptions) {
                        original_options = _.get(scope, selectOptions);
                    }

                $.fn.select2.amd.require([
                    'select2/utils',
                    'select2/dropdown',
                    'select2/dropdown/search',
                    'select2/dropdown/attachContainer',
                    'select2/dropdown/closeOnSelect',
                    'select2/dropdown/minimumResultsForSearch',
                    'select2/data/tokenizer'
                ], function(Utils, Dropdown, Search, AttachContainer, CloseOnSelect, MinimumResultsForSearch, Tokenizer) {

                    var CustomAdapter =
                        _.reduce([Search, AttachContainer, CloseOnSelect, MinimumResultsForSearch, Tokenizer],
                            function(Adapter, Decorator) {
                                return Utils.Decorate(Adapter, Decorator);
                            }, Dropdown);

                    var config = {
                        placeholder: placeholder,
                        multiple: multiple,
                        containerCssClass: 'Form-dropDown',
                        width: '100%',
                        minimumResultsForSearch: minimumResultsForSearch,
                        escapeMarkup: function(m) {
                            return $filter('sanitize')(m);
                        }
                    };

                    // multiple-choice directive calls select2 but needs to do so without this custom adapter
                    // to allow the element to be draggable on survey preview.
                    if (customDropdownAdapter) {
                        config.dropdownAdapter = CustomAdapter;
                    }

                    if (addNew) {
                        config.tags = true;
                        config.tokenSeparators = [];

                        if (!multiple) {
                            config.minimumResultsForSearch = 1;
                            config.matcher = function(params, data) {
                                // If there are no search terms, return all of the data
                                if ($.trim(params.term) === '' &&
                                    data.text.indexOf("Choose an") === -1) {
                                        return data;
                                }

                                // Do not display the item if there is no 'text' property
                                if (typeof data.text === 'undefined' ||
                                    data.text.indexOf("Choose an") > -1) {
                                  return null;
                                }

                                // Return `null` if the term should not be displayed
                                return null;
                            };
                        }
                    }

                    $(element).select2(config);

                    // Don't toggle the dropdown when a multiselect option is
                    // being removed
                    if (multiple) {
                        $(element).on('select2:opening', (e) => {
                            var unselecting = $(e.target).data('select2-unselecting');
                            if (unselecting === true) {
                                $(e.target).removeData('select2-unselecting');
                                e.preventDefault();
                            }
                        }).on('select2:unselecting', (e) => {
                            $(e.target).data('select2-unselecting', true);
                        });
                    }

                    if (addNew && !multiple) {
                        $(element).on('select2:select', (e) => {
                            _.set(scope, model, e.params.data.text);
                            const optionsClone = _.clone(original_options);
                            _.set(scope, selectOptions, optionsClone);
                            if (e.params.data.id === "") {
                                return;
                            }
                            const optionMatches = original_options.findIndex((option) => option === e.params.data.text);
                            if (optionMatches === -1) {
                                optionsClone.push(e.params.data.text);
                                _.set(scope, selectOptions, optionsClone);
                            }
                            $(element).select2(config);
                        });
                    }

                    if (options) {
                        for (var d = 0; d < $(element + " option").length; d++) {
                            var item = $(element + " option")[d];
                            for (var f = 0; f < options.length; f++) {
                                if (item.value === options[f].id) {
                                    // Append it to the select
                                    item.setAttribute('selected', 'selected');
                                }
                            }
                        }

                        $(element).trigger('change');
                    }
                    defer.resolve("select2 loaded");
                });

                return defer.promise;
            };
        }
    ])
    /**
     * @ngdoc method
     * @name shared.function:Utilities#GetChoices
     * @methodOf shared.function:Utilities
     * @description Make an Options call to the API and retrieve dropdown options
     * GetChoices({
     *     scope:       Parent $scope
     *     url:         API resource to access
     *     field:       API element in the response object that contains the option list.
     *     variable:    Scope variable that will receive the list.
     *     callback:    Optional. Will issue scope.$emit(callback) on completion.
     *     choice_name: Optional. Used when list is found in a variable other than 'choices'.
     * })
     */
    .factory('GetChoices', ['Rest', 'ProcessErrors',
        function(Rest, ProcessErrors) {
            return function(params) {
                var scope = params.scope,
                    url = params.url,
                    field = params.field,
                    variable = params.variable,
                    callback = params.callback,
                    choice_name = params.choice_name,
                    options = params.options;

                if (scope[variable]) {
                    scope[variable].length = 0;
                } else {
                    scope[variable] = [];
                }

                var withOptions = function(options) {
                    var choices, defaultChoice;
                    choices = (choice_name) ? options.actions.GET[field][choice_name] : options.actions.GET[field].choices;
                    if (options && options.actions && options.actions.POST && options.actions.POST[field]) {
                        defaultChoice = options.actions.POST[field].default;
                    }
                    if (choices) {
                        // including 'name' property so list can be used by search
                        choices.forEach(function(choice) {
                            scope[variable].push({
                                label: choice[1],
                                value: choice[0],
                                name: choice[1]
                            });
                        });
                    }
                    if (defaultChoice !== undefined) {
                        var val;
                        for (val in scope[variable]) {
                            if (scope[variable][val].value === defaultChoice) {
                                scope[variable][val].isDefault = true;
                            }
                        }
                    }
                    if (callback) {
                        scope.$emit(callback);
                    }
                };

                if (!options) {
                  Rest.setUrl(url);
                  Rest.options()
                      .then(({data}) => {
                          withOptions(data);
                      })
                      .catch(({data, status}) => {
                          ProcessErrors(scope, data, status, null, {
                              hdr: 'Error!',
                              msg: 'Failed to get ' + url + '. OPTIONS status: ' + status
                          });
                      });
                } else {
                  withOptions(options);
                }
            };
        }
    ])

/**
 * @ngdoc method
 * @name shared.function:Utilities#Find
 * @methodOf shared.function:Utilities
 * @description
 * Search an array of objects, returning the matchting object or null
 *
 *  Find({ list: [], key: "key", val: <key value> });
 */
.factory('Find', [
    function() {
        return function(params) {
            var list = params.list,
                key = params.key,
                val = params.val,
                found = false,
                i;
            if (typeof list === 'object' && Array.isArray(list)) {
                for (i = 0; i < params.list.length; i++) {
                    if (list[i][key] === val) {
                        found = true;
                        break;
                    }
                }
                return (found) ? list[i] : null;
            }
            return null;
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#DebugForm
 * @methodOf shared.function:Utilities
 * @description
 * DebugForm({ form: <form object>, scope: <current scope object> });
 *
 * Use to log the $pristine and $valid properties of each form element. Helpful when form
 * buttons fail to enable/disable properly.
 *
 */
.factory('DebugForm', [
    function() {
        return function(params) {
            var form = params.form,
                scope = params.scope,
                fld;
            for (fld in form.fields) {
                if (scope[form.name + '_form'][fld]) {
                    console.log(fld + ' valid: ' + scope[form.name + '_form'][fld].$valid);
                }
                if (form.fields[fld].sourceModel) {
                    if (scope[form.name + '_form'][form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField]) {
                        console.log(form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField + ' valid: ' +
                            scope[form.name + '_form'][form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField].$valid);
                    }
                }
            }
            console.log('form pristine: ' + scope[form.name + '_form'].$pristine);
            console.log('form valid: ' + scope[form.name + '_form'].$valid);
        };
    }
])


/**
 * @ngdoc method
 * @name shared.function:Utilities#Store
 * @methodOf shared.function:Utilities
 * @description Store
 *
 * Wrapper for local storage. All local storage requests flow through here so that we can
 * stringify/unstringify objects and respond to future issues in one place. For example,
 * we may at some point want to only use session storage rather than local storage. We might
 * want to add a test for whether or not local/session storage exists for the browser, etc.
 *
 * store(key,value) will store the value using the key
 *
 * store(key) retrieves the value of the key
 * discuss use case
 */
.factory('Store', ['Empty',
    function(Empty) {
        return function(key, value) {
            if (!Empty(value)) {
                // Store the value
                localStorage[key] = JSON.stringify(value);
            } else if (!Empty(key)) {
                // Return the value
                var val = localStorage[key];
                return (!Empty(val)) ? JSON.parse(val) : null;
            }
        };
    }
])

/**
 * @ngdoc method
 * @name shared.function:Utilities#ApplyEllipsis
 * @methodOf shared.function:Utilities
 * @description
 * ApplyEllipsis()
 * discuss significance
 */
.factory('ApplyEllipsis', [
        function() {
            return function(selector) {
                // Add a hidden element to the DOM. We'll use this to calc the px length of
                // our target text.
                var tmp = $('#string-test');
                if (!tmp.length) {
                    $('body').append('<div style="display:none;" id="string-test"></div>');
                    tmp = $('#string-test');
                }
                // Find and process the text.
                $(selector).each(function() {
                    var setTitle = true,
                        txt, w, pw, cw, df;
                    if ($(this).attr('title')) {
                        txt = $(this).attr('title');
                        setTitle = false;
                    } else {
                        txt = $(this).text();
                    }
                    tmp.text(txt);
                    w = tmp.width(); //text width
                    pw = $(this).parent().width(); //parent width
                    if (w > pw) {
                        // text is wider than parent width
                        if (setTitle) {
                            // Save the original text in the title
                            $(this).attr('title', txt);
                        }
                        cw = w / txt.length; // px width per character
                        df = w - pw; // difference in px
                        txt = txt.substr(0, txt.length - (Math.ceil(df / cw) + 3));
                        $(this).text(txt + '...');
                    }
                    if (pw > w && !setTitle) {
                        // the parent has expanded and we previously set the title text
                        txt = $(this).attr('title');
                        $(this).text(txt);
                    }
                });

            };
        }
    ])
    .factory('ParamPass', function() {
        var savedData;

        function set(data) {
            savedData = data;
        }

        function get() {
            var returnData = savedData;
            savedData = undefined;
            return returnData;
        }

        return {
            set: set,
            get: get
        };
    });
