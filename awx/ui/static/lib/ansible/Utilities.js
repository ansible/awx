/************************************
 *
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  Utility functions
 *
 */

/* jshint devel:true */

'use strict';

angular.module('Utilities', ['RestServices', 'Utilities'])

/*
 *  Place to remove things that might be lingering from a prior tab or view.
 *  This used to destroy the scope, but that causes issues in angular 1.2.x
 */
.factory('ClearScope', [
    function () {
        return function () {
            $('.tooltip').each(function () {
                $(this).remove();
            });

            $('.popover').each(function () {
                $(this).remove();
            });

            try {
                $('#help-modal').dialog('close');
            } catch (e) {
                // ignore
            }
            $(window).unbind('resize');
        };
    }
])


/* Empty()
 *
 * Test if a value is 'empty'. Returns true if val is null | '' | undefined.
 * Only works on non-Ojbect types.
 *
 */
.factory('Empty', [
    function () {
        return function (val) {
            return (val === null || val === undefined || val === '') ? true : false;
        };
    }
])


.factory('ToggleClass', function () {
    return function (selector, cssClass) {
        // Toggles the existance of a css class on a given element   
        if ($(selector) && $(selector).hasClass(cssClass)) {
            $(selector).removeClass(cssClass);
        } else if ($(selector)) {
            $(selector).addClass(cssClass);
        }
    };
})


/* 
 * Pass in the header and message you want displayed on TB modal dialog found in index.html.
 * Assumes an #id of 'alert-modal'. Pass in an optional TB alert class (i.e. alert-danger, alert-success,
 * alert-info...). Pass an optional function(){}, if you want a specific action to occur when user
 * clicks 'OK' button. Set secondAlert to true, when a second dialog is needed.
 */
.factory('Alert', ['$rootScope',
    function ($rootScope) {
        return function (hdr, msg, cls, action, secondAlert, disableButtons) {
            if (secondAlert) {
                $rootScope.alertHeader2 = hdr;
                $rootScope.alertBody2 = msg;
                $rootScope.alertClass2 = (cls) ? cls : 'alert-danger'; //default alert class is alert-danger
                $('#alert-modal2').modal({
                    show: true,
                    keyboard: true,
                    backdrop: 'static'
                });
                $rootScope.disableButtons2 = (disableButtons) ? true : false;
                
                $('#alert-modal2').on('hidden.bs.modal', function () {
                    if (action) {
                        action();
                    }
                });
                $(document).bind('keydown', function (e) {
                    if (e.keyCode === 27) {
                        $('#alert-modal2').modal('hide');
                    }
                });
            } else {
                $rootScope.alertHeader = hdr;
                $rootScope.alertBody = msg;
                $rootScope.alertClass = (cls) ? cls : 'alert-danger'; //default alert class is alert-danger
                $('#alert-modal').modal({
                    show: true,
                    keyboard: true,
                    backdrop: 'static'
                });

                $('#alert-modal').on('hidden.bs.modal', function () {
                    if (action) {
                        action();
                    }
                });

                $(document).bind('keydown', function (e) {
                    if (e.keyCode === 27) {
                        $('#alert-modal').modal('hide');
                    }
                });

                $rootScope.disableButtons = (disableButtons) ? true : false;
            }
        };
    }
])


.factory('ProcessErrors', ['$rootScope', '$cookieStore', '$log', '$location', 'Alert', 'Wait',
    function ($rootScope, $cookieStore, $log, $location, Alert, Wait) {
        return function (scope, data, status, form, defaultMsg) {
            var field, fieldErrors, msg;
            Wait('stop');
            if ($AnsibleConfig.debug_mode && console) {
                console.log('Debug status: ' + status);
                console.log('Debug data: ');
                console.log(data);
            }
            if (status === 403) {
                msg = 'The API responded with a 403 Access Denied error. ';
                if (data.detail) {
                    msg += 'Detail: ' + data.detail;
                } else {
                    msg += 'Please contact your system administrator.';
                }
                Alert(defaultMsg.hdr, msg);
            } else if ((status === 401 && data.detail && data.detail === 'Token is expired') ||
                (status === 401 && data.detail && data.detail === 'Invalid token')) {
                $rootScope.sessionTimer.expireSession();
                $location.url('/login');
            } else if (data.non_field_errors) {
                Alert('Error!', data.non_field_errors);
            } else if (data.detail) {
                Alert(defaultMsg.hdr, defaultMsg.msg + ' ' + data.detail);
            } else if (data.__all__) {
                Alert('Error!', data.__all__);
            } else if (form) {
                fieldErrors = false;
                for (field in form.fields) {
                    if (data[field] && form.fields[field].tab) {
                        // If the form is part of a tab group, activate the tab
                        $('#' + form.name + "_tabs a[href=\"#" + form.fields[field].tab + '"]').tab('show');
                    }
                    if (form.fields[field].realName) {
                        if (data[form.fields[field].realName]) {
                            scope[field + '_api_error'] = data[form.fields[field]][0];
                            //scope[form.name + '_form'][form.fields[field].realName].$setValidity('apiError', false);
                            $('[name="' + form.fields[field].realName + '"]').addClass('ng-invalid');
                            fieldErrors = true;
                        }
                    }
                    if (form.fields[field].sourceModel) {
                        if (data[field]) {
                            scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '_api_error'] =
                                data[field][0];
                            //scope[form.name + '_form'][form.fields[field].sourceModel + '_' + form.fields[field].sourceField].$setValidity('apiError', false);
                            $('[name="' + form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '"]').addClass('ng-invalid');
                            fieldErrors = true;
                        }
                    } else {
                        if (data[field]) {
                            scope[field + '_api_error'] = data[field][0];
                            //scope[form.name + '_form'][field].$setValidity('apiError', false);
                            $('[name="' + field + '"]').addClass('ng-invalid');
                            fieldErrors = true;
                        }
                    }
                }
                if ((!fieldErrors) && defaultMsg) {
                    Alert(defaultMsg.hdr, defaultMsg.msg);
                }
            } else {
                Alert(defaultMsg.hdr, defaultMsg.msg);
            }
        };
    }
])


.factory('LoadBreadCrumbs', ['$rootScope', '$routeParams', '$location', 'Empty',
    function ($rootScope, $routeParams, $location, Empty) {
        return function (crumb) {

            var title, found, j, i, paths, ppath, parent, child;

            function toUppercase(a) {
                return a.toUpperCase();
            }

            function singular(a) {
                return (a === 'ies') ? 'y' : '';
            }

            //Keep a list of path/title mappings. When we see /organizations/XX in the path, for example, 
            //we'll know the actual organization name it maps to.
            if (!Empty(crumb)) {
                found = false;
                //crumb.title = crumb.title.charAt(0).toUpperCase() + crumb.title.slice(1);
                for (i = 0; i < $rootScope.crumbCache.length; i++) {
                    if ($rootScope.crumbCache[i].path === crumb.path) {
                        found = true;
                        $rootScope.crumbCache[i] = crumb;
                        break;
                    }
                }
                if (!found) {
                    $rootScope.crumbCache.push(crumb);
                }
            }

            paths = $location.path().replace(/^\//, '').split('/');
            ppath = '';
            $rootScope.breadcrumbs = [];
            if (paths.length > 1) {
                for (i = 0; i < paths.length - 1; i++) {
                    if (i > 0 && paths[i].match(/\d+/)) {
                        parent = paths[i - 1];
                        child = parent.replace(/(ies$|s$)/, singular);
                        child = child.charAt(0).toUpperCase() + child.slice(1);
                        // find the correct title
                        found = false;
                        for (j = 0; j < $rootScope.crumbCache.length; j++) {
                            if ($rootScope.crumbCache[j].path === '/' + parent + '/' + paths[i]) {
                                child = $rootScope.crumbCache[j].title;
                                found = true;
                                break;
                            }
                        }

                        if (found && $rootScope.crumbCache[j].altPath !== undefined) {
                            // Use altPath to override default path construction
                            $rootScope.breadcrumbs.push({
                                title: child,
                                path: $rootScope.crumbCache[j].altPath
                            });
                        } else {
                            $rootScope.breadcrumbs.push({
                                title: child,
                                path: ppath + '/' + paths[i]
                            });
                        }
                    } else {
                        //if (/_/.test(paths[i])) {
                            // replace '_' with space and uppercase each word
                            
                        //}
                        //title = paths[i].charAt(0).toUpperCase() + paths[i].slice(1);
                        title = paths[i].replace(/(?:^|_)\S/g, toUppercase).replace(/_/g, ' ');
                        $rootScope.breadcrumbs.push({
                            title: title,
                            path: ppath + '/' + paths[i]
                        });
                    }
                    ppath += '/' + paths[i];
                }
            }
        };
    }
])


/* Display a help dialog
 *
 * HelpDialog({ defn: <HelpDefinition> })
 *
 */
.factory('HelpDialog', ['$rootScope', '$location', 'Store',
    function ($rootScope, $location, Store) {
        return function (params) {
            
            var defn = params.defn,
                current_step = params.step,
                autoShow = params.autoShow || false;

            function showHelp(step) {

                var btns, ww, width, height, isOpen = false;
                current_step = step;

                function buildHtml(step) {
                    var html = '';
                    //html += (step.intro) ? "<div class=\"help-intro\">" + step.intro + "</div>" : "";
                    html += "<h4>" + step.intro + "</h4>\n";
                    html += "<div class=\"img-container\">\n";
                    html += "<img src=\"" + $basePath + "img/help/" + step.img.src + "\" >";
                    html += "</div>\n";
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
                    isOpen = $('#help-modal').dialog('isOpen');
                } catch (e) {
                    // ignore
                }

                if (isOpen) {
                    $('#help-modal').html(buildHtml(defn.story.steps[current_step]));
                } else {
                    // Define buttons based on story length
                    btns = [];
                    if (defn.story.steps.length > 1) {
                        btns.push({
                            text: "Prev",
                            click: function (e) {
                                if (current_step - 1 === 0) {
                                    $(e.target).button('disable');
                                }
                                if (current_step - 1 < defn.story.steps.length - 1) {
                                    $(e.target).next().button('enable');
                                }
                                showHelp(current_step - 1);
                            },
                            disabled: true
                        });
                        btns.push({
                            text: "Next",
                            click: function (e) {
                                if (current_step + 1 > 0) {
                                    $(e.target).prev().button('enable');
                                }
                                if (current_step + 1 === defn.story.steps.length - 1) {
                                    $(e.target).button('disable');
                                }
                                showHelp(current_step + 1);
                            }
                        });
                    }
                    btns.push({
                        text: "Close",
                        click: function () {
                            $('#help-modal').dialog('close');
                        }
                    });
                    // Show the dialog
                    $('#help-modal').html(buildHtml(defn.story.steps[current_step])).dialog({
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
                        close: function () {
                            $('#help-modal').empty();
                        }
                    });

                    // Make the buttons look like TB and add FA icons
                    $('.ui-dialog-buttonset button').each(function () {
                        var c, h, l;
                        l = $(this).text();
                        if (l === 'Close') {
                            h = "fa-times";
                            c = "btn btn-default";
                            $(this).attr({
                                'class': c
                            }).html("<i class=\"fa " + h + "\"></i> Close");
                        } else if (l === 'Prev') {
                            h = "fa-chevron-left";
                            c = "btn btn-primary";
                            $(this).attr({
                                'class': c
                            }).html("<i class=\"fa " + h + "\"></i> Prev");
                        } else {
                            h = "fa-chevron-right";
                            c = "btn btn-primary";
                            $(this).attr({
                                'class': c
                            }).html("Next <i class=\"fa " + h + "\"></i>").css({
                                'margin-right': '20px'
                            });
                        }
                    });

                    $('.ui-dialog[aria-describedby="help-modal"]').find('.ui-dialog-titlebar button')
                        .empty().attr({
                            'class': 'close'
                        }).text('x');

                    // If user clicks the checkbox, update local storage
                    $('#auto-off-checkbox').click(function () {
                        if ($('input[name="auto-off-checkbox"]:checked').length) {
                            Store('inventoryAutoHelp', 'off');
                        } else {
                            Store('inventoryAutoHelp', 'on');
                        }
                    });
                }
            }

            showHelp(0);

        };
    }
])


/* 
 * Split the current path by '/' and use the array elements from 0 up to and
 * including idx as the new path.  If no idx value supplied, use 0 to length - 1.  
 *
 */
.factory('ReturnToCaller', ['$location', 'Empty',
    function ($location, Empty) {
        return function (idx) {
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


/*
 * Wrapper for data filter- an attempt to insure all dates display in
 * the same format. Pass in date object or string. See: http://docs.angularjs.org/api/ng.filter:date
 */
.factory('FormatDate', ['$filter',
    function ($filter) {
        return function (dt) {
            return $filter('date')(dt, 'MM/dd/yy HH:mm:ss');
        };
    }
])

/* 
 * Display a spinning icon in the center of the screen to freeze the 
 * UI while waiting on async things to complete (i.e. API calls).    
 * Wait('start' | 'stop');
 *
 */
.factory('Wait', ['$rootScope',
    function ($rootScope) {
        return function (directive) {
            var docw, doch, spinnyw, spinnyh, x, y;
            if (directive === 'start' && !$rootScope.waiting) {
                $rootScope.waiting = true;
                docw = $(window).width();
                doch = $(window).height();
                spinnyw = $('.spinny').width();
                spinnyh = $('.spinny').height();
                x = (docw - spinnyw) / 2;
                y = (doch - spinnyh) / 2;
                $('.overlay').css({
                    width: $(document).width(),
                    height: $(document).height()
                }).fadeIn();
                $('.spinny').css({
                    top: y,
                    left: x
                }).fadeIn(400);
            } else if (directive === 'stop' && $rootScope.waiting) {
                $('.spinny, .overlay').fadeOut(400, function () {
                    $rootScope.waiting = false;
                });
            }
        };
    }
])

.factory('HideElement', [
    function () {
        return function (selector, action) {
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
    function () {
        return function () {
            // And Fade-out the cloack revealing the element
            $('#curtain-div').fadeOut(500, function () {
                $(this).remove();
            });
        };
    }
])

/* 
 * Make an Options call to the API and retrieve dropdown options
 *
 */
.factory('GetChoices', ['Rest', 'ProcessErrors',
    function (Rest, ProcessErrors) {
        return function (params) {
            var scope = params.scope,
                url = params.url,
                field = params.field,
                variable = params.variable,
                callback = params.callback, // Optional. Provide if you want scop.$emit on completion. 
                choice_name = params.choice_name; // Optional. Used when data is in something other than 'choices'

            if (scope[variable]) {
                scope[variable].length = 0;
            } else {
                scope[variable] = [];
            }

            Rest.setUrl(url);
            Rest.options()
                .success(function (data) {
                    var choices, i;
                    choices = (choice_name) ? data.actions.GET[field][choice_name] : data.actions.GET[field].choices;
                    // including 'name' property so list can be used by search
                    for (i = 0; i < choices.length; i++) {
                        scope[variable].push({
                            label: choices[i][1],
                            value: choices[i][0],
                            name: choices[i][1]
                        });
                    }
                    if (callback) {
                        scope.$emit(callback);
                    }
                })
                .error(function (data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get ' + url + '. GET status: ' + status });
                });
        };
    }
])

/*
 * Search an array of objects, returning the matchting object or null
 *
 *  Find({ list: [], key: "key", val: <key value> });
 */
.factory('Find', [
    function () {
        return function (params) {
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

/* 
 * DeugForm({ form: <form object>, scope: <current scope object> });
 *
 * Use to log the $pristine and $valid properties of each form element. Helpful when form
 * buttons fail to enable/disable properly.
 *
 */
.factory('DebugForm', [
    function () {
        return function (params) {
            var form = params.form,
                scope = params.scope,
                fld;
            console.log('here');
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


/* Store
 *
 * Wrapper for local storage. All local storage requests flow through here so that we can
 * stringify/unstringify objects and respond to future issues in one place. For example,
 * we may at some point want to only use session storage rather than local storage. We might
 * want to add a test for whether or not local/session storage exists for the browser, etc.
 *
 * store(key,value) will store the value using the key
 *
 * store(key) retrieves the value of the key
 *
 */
.factory('Store', ['Empty',
    function (Empty) {
        return function (key, value) {
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

/*
 *
 * ApplyEllipsis()
 *
 */
.factory('ApplyEllipsis', [
    function () {
        return function (selector) {
            // Add a hidden element to the DOM. We'll use this to calc the px length of 
            // our target text.
            var tmp = $('#string-test');
            if (!tmp.length) {
                $('body').append('<div style="display:none;" id="string-test"></div>');
                tmp = $('#string-test');
            }
            // Find and process the text.
            $(selector).each(function () {
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
]);