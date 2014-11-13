/***************************************************************************
 * angular-scheruler.js
 *
 * Copyright (c) 2014 Ansible, Inc.
 *
 * Maintainers:
 *
 * Chris Houseknecht
 *   @chouseknecht
 *   chouse@ansible.com
 *
 */

/* global RRule */

'use strict';


angular.module('underscore',[])
    .factory('_', [ function() {
        return window._;
    }]);


angular.module('AngularScheduler', ['underscore'])

    .constant('AngularScheduler.partials', '/lib/')
    .constant('AngularScheduler.useTimezone', false)
    .constant('AngularScheduler.showUTCField', false)

    // Initialize supporting scope variables and functions. Returns a scheduler object with getString(),
    // setString() and inject() methods.
    .factory('SchedulerInit', ['$log', '$filter', '$timezones', 'LoadLookupValues', 'SetDefaults', 'CreateObject', '_',
    'AngularScheduler.useTimezone', 'AngularScheduler.showUTCField', 'InRange',
    function($log, $filter, $timezones, LoadLookupValues, SetDefaults, CreateObject, _, useTimezone, showUTCField, InRange) {
        return function(params) {

            var scope = params.scope,
                requireFutureStartTime = params.requireFutureStartTime || false;

            scope.schedulerShowTimeZone = useTimezone;
            scope.schedulerShowUTCStartTime = showUTCField;

            scope.setDefaults = function() {
                if (useTimezone) {
                    scope.current_timezone = $timezones.getLocal();
                    if ($.isEmptyObject(scope.current_timezone) || !scope.current_timezone.name) {
                        $log.error('Failed to find local timezone. Defaulting to America/New_York.');
                        scope.current_timezone = { name: 'America/New_York' };
                    }
                    // Set the <select> to the browser's local timezone
                    scope.schedulerTimeZone = _.find(scope.timeZones, function(x) {
                        return x.name === scope.current_timezone.name;
                    });
                }
                LoadLookupValues(scope);
                SetDefaults(scope);
                scope.scheduleTimeChange();
                scope.scheduleRepeatChange();
            };

            scope.scheduleTimeChange = function() {
                if (scope.schedulerStartDt === "" || scope.schedulerStartDt === null || scope.schedulerStartDt === undefined) {
                    scope.startDateError("Provide a valid start date and time");
                    scope.schedulerUTCTime = '';
                }
                else if ( !(InRange(scope.schedulerStartHour, 0, 23, 2) && InRange(scope.schedulerStartMinute, 0, 59, 2) && InRange(scope.schedulerStartSecond, 0, 59, 2)) ) {
                    scope.scheduler_startTime_error = true;
                }
                else {
                    if (useTimezone) {
                        scope.resetStartDate();
                        try {
                            var dateStr = scope.schedulerStartDt.replace(/(\d{2})\/(\d{2})\/(\d{4})/, function(match, p1, p2, p3) {
                                    return p3 + '-' + p1 + '-' + p2;
                                });
                            dateStr += 'T' + $filter('schZeroPad')(scope.schedulerStartHour, 2) + ':' + $filter('schZeroPad')(scope.schedulerStartMinute, 2) + ':' +
                                $filter('schZeroPad')(scope.schedulerStartSecond, 2) + '.000Z';
                            scope.schedulerUTCTime = $filter('schDateStrFix')($timezones.toUTC(dateStr, scope.schedulerTimeZone.name).toISOString());
                            scope.scheduler_form_schedulerStartDt_error = false;
                            scope.scheduler_startTime_error = false;
                        }
                        catch(e) {
                            scope.startDateError("Provide a valid start date and time");
                        }
                    }
                    else {
                        scope.scheduler_startTime_error = false;
                        scope.scheduler_form_schedulerStartDt_error = false;
                        scope.schedulerUTCTime = $filter('schDateStrFix')(scope.schedulerStartDt + 'T' + scope.schedulerStartHour + ':' + scope.schedulerStartMinute +
                            ':' + scope.schedulerStartSecond + '.000Z');
                    }
                }
            };

            scope.resetError = function(variable) {
                scope[variable] = false;
            };

            scope.scheduleRepeatChange = function() {
                if (scope.schedulerFrequency && scope.schedulerFrequency.value !== '' && scope.schedulerFrequency.value !== 'none') {
                    scope.schedulerInterval = 1;
                    scope.schedulerShowInterval = true;
                    scope.schedulerIntervalLabel = scope.schedulerFrequency.intervalLabel;
                }
                else {
                    scope.schedulerShowInterval = false;
                    scope.schedulerEnd = scope.endOptions[0];
                }
                scope.sheduler_frequency_error = false;
            };

            scope.showCalendar = function(fld) {
                $('#' + fld).focus();
            };

            scope.monthlyRepeatChange = function() {
                if (scope.monthlyRepeatOption !== 'day') {
                    $('#monthDay').spinner('disable');
                }
                else {
                    $('#monthDay').spinner('enable');
                }
            };

            scope.yearlyRepeatChange = function() {
                if (scope.yearlyRepeatOption !== 'month') {
                    $('#yearlyRepeatDay').spinner('disable');
                }
                else {
                    $('#yearlyRepeatDay').spinner('enable');
                }
            };

            scope.setWeekday = function(event, day) {
                // Add or remove day when user clicks checkbox button
                var i = scope.weekDays.indexOf(day);
                if (i >= 0) {
                    scope.weekDays.splice(i,1);
                }
                else {
                    scope.weekDays.push(day);
                }
                $(event.target).blur();
                scope.scheduler_weekDays_error = false;
            };

            scope.startDateError = function(msg) {
                if (scope.scheduler_form) {
                    if (scope.scheduler_form.schedulerStartDt) {
                        scope.scheduler_form_schedulerStartDt_error = msg;
                        scope.scheduler_form.schedulerStartDt.$pristine = false;
                        scope.scheduler_form.schedulerStartDt.$dirty = true;
                    }
                    $('#schedulerStartDt').removeClass('ng-pristine').removeClass('ng-valid').removeClass('ng-valid-custom-error')
                        .addClass('ng-dirty').addClass('ng-invalid').addClass('ng-invalid-custom-error');
                }
            };

            scope.resetStartDate = function() {
                if (scope.scheduler_form) {
                    scope.scheduler_form_schedulerStartDt_error = '';
                    if (scope.scheduler_form.schedulerStartDt) {
                        scope.scheduler_form.schedulerStartDt.$setValidity('custom-error', true);
                        scope.scheduler_form.schedulerStartDt.$setPristine();
                    }
                }
            };

            scope.schedulerEndChange = function() {
                var dt = new Date(), // date adjusted to local zone automatically
                    month = $filter('schZeroPad')(dt.getMonth() + 1, 2),
                    day = $filter('schZeroPad')(dt.getDate(), 2);
                scope.schedulerEndDt = month + '/' + day + '/' + dt.getFullYear();
                scope.schedulerOccurrenceCount = 1;
            };

            // When timezones become available, use to set defaults
            if (scope.removeZonesReady) {
                scope.removeZonesReady();
            }
            scope.removeZonesReady = scope.$on('zonesReady', function() {
                scope.timeZones = JSON.parse(localStorage.zones);
                scope.setDefaults();
            });

            if (useTimezone) {
                // Build list of timezone <select> element options
                $timezones.getZoneList(scope);
            }
            else {
                scope.setDefaults();
            }

            return CreateObject(scope, requireFutureStartTime);

        };
    }])

    /**
       Return an AngularScheduler object we can use to get the RRule result from user input, check if
       user input is valid, reset the form, etc. All the things we need to access and manipulate the
       scheduler widget
     */
    .factory('CreateObject', ['AngularScheduler.useTimezone', '$filter', 'GetRule', 'Inject', 'InjectDetail', 'SetDefaults', '$timezones', 'SetRule', 'InRange',
    function(useTimezone, $filter, GetRule, Inject, InjectDetail, SetDefaults, $timezones, SetRule, InRange) {
        return function(scope, requireFutureST) {
            var fn = function() {

                this.scope = scope;
                this.useTimezone = useTimezone;
                this.requireFutureStartTime = requireFutureST;

                // Evaluate user intput and build options for passing to rrule
                this.getOptions = function() {
                    var options = {};
                    options.startDate = this.scope.schedulerUTCTime;
                    options.frequency = this.scope.schedulerFrequency.value;
                    options.interval = this.scope.schedulerInterval;
                    if (this.scope.schedulerEnd.value === 'after') {
                        options.occurrenceCount = this.scope.schedulerOccurrenceCount;
                    }
                    if (this.scope.schedulerEnd.value === 'on') {
                        options.endDate = scope.schedulerEndDt.replace(/(\d{2})\/(\d{2})\/(\d{4})/, function(match, p1, p2, p3) {
                                    return p3 + '-' + p1 + '-' + p2;
                                }) + 'T' + this.scope.schedulerUTCTime.replace(/\d{2}\/\d{2}\/\d{4} /,'').replace(/ UTC/,'') + 'Z';
                    }
                    if (this.scope.schedulerFrequency.value === 'weekly') {
                        options.weekDays = this.scope.weekDays;
                    }
                    else if (this.scope.schedulerFrequency.value === 'yearly') {
                        if (this.scope.yearlyRepeatOption === 'month') {
                            options.month = this.scope.yearlyMonth.value;
                            options.monthDay = this.scope.yearlyMonthDay;
                        }
                        else {
                            options.setOccurrence = this.scope.yearlyOccurrence.value;
                            options.weekDays = this.scope.yearlyWeekDay.value;
                            options.month = this.scope.yearlyOtherMonth.value;
                        }
                    }
                    else if (this.scope.schedulerFrequency.value === 'monthly') {
                        if (this.scope.monthlyRepeatOption === 'day') {
                            options.monthDay = this.scope.monthDay;
                        }
                        else {
                            options.setOccurrence = this.scope.monthlyOccurrence.value;
                            options.weekDays = this.scope.monthlyWeekDay.value;
                        }
                    }
                    return options;
                };

                // Clear custom field errors
                this.clearErrors = function() {
                    this.scope.scheduler_weekDays_error = false;
                    this.scope.scheduler_endDt_error = false;
                    this.scope.resetStartDate();
                    this.scope.scheduler_endDt_error = false;
                    this.scope.scheduler_interval_error = false;
                    this.scope.scheduler_occurrenceCount_error = false;
                    this.scope.scheduler_monthDay_error = false;
                    this.scope.scheduler_yearlyMonthDay_error = false;

                    if (this.scope.scheduler_form && this.scope.scheduler_form.schedulerEndDt) {
                        this.scope.scheduler_form.schedulerEndDt.$setValidity('custom-error', true);
                        this.scope.scheduler_form.schedulerEndDt.$setPristine();
                        this.scope.scheduler_form.$setPristine();
                    }
                };

                // Set values for detail page
                this.setDetails = function() {
                    var rrule = this.getRRule(),
                        scope = this.scope;
                    if (rrule) {
                        scope.rrule_nlp_description = rrule.toText();
                        scope.dateChoice = 'local';
                        scope.occurrence_list = [];
                        rrule.all(function(date, i){
                            var local, dt;
                            if (i < 10) {
                                if (useTimezone) {
                                    dt = $timezones.align(date, scope.schedulerTimeZone.name);
                                    local = $filter('schZeroPad')(dt.getMonth() + 1,2) + '/' +
                                        $filter('schZeroPad')(dt.getDate(),2) + '/' + dt.getFullYear() + ' ' +
                                        $filter('schZeroPad')(dt.getHours(),2) + ':' +
                                        $filter('schZeroPad')(dt.getMinutes(),2) + ':' +
                                        $filter('schZeroPad')(dt.getSeconds(),2) + ' ' +
                                        dt.getTimezoneAbbreviation();
                                }
                                else {
                                    local = $filter('date')(date, 'MM/dd/yyyy HH:mm:ss Z');
                                }
                                scope.occurrence_list.push({ utc: $filter('schDateStrFix')(date.toISOString()), local: local });
                                return true;
                            }
                            return false;
                        });
                        scope.rrule_nlp_description = rrule.toText().replace(/^RRule error.*$/,'Natural language description not available');
                        scope.rrule = rrule.toString();
                    }
                };

                // Check the input form for errors
                this.isValid = function() {
                    var startDt, now, dateStr, adjNow, timeNow, timeFuture, validity = true;
                    this.clearErrors();

                    if (this.scope.schedulerFrequency.value !== 'none' && !InRange(this.scope.schedulerInterval, 1, 999, 3)) {
                        this.scope.scheduler_interval_error = true;
                        validity = false;
                    }

                    if (this.scope.schedulerEnd.value === 'after' && !InRange(this.scope.schedulerOccurrenceCount, 1, 999, 3)) {
                        this.scope.scheduler_occurrenceCount_error = true;
                        validity = false;
                    }

                    if (this.scope.schedulerFrequency.value === 'weekly' && this.scope.weekDays.length === 0) {
                        this.scope.scheduler_weekDays_error = true;
                        validity = false;
                    }

                    if (this.scope.schedulerFrequency.value === 'monthly' && this.scope.monthlyRepeatOption === 'day' && !InRange(this.scope.monthDay, 1, 31, 99)) {
                        this.scope.scheduler_monthDay_error = true;
                        validity = false;
                    }

                    if (this.scope.schedulerFrequency.value === 'yearly' && this.scope.yearlyRepeatOption === 'month' && !InRange(this.scope.yearlyMonthDay, 1, 31, 99)) {
                        this.scope.scheduler_yearlyMonthDay_error = true;
                        validity = false;
                    }
                    if ( !(InRange(scope.schedulerStartHour, 0, 23, 2) && InRange(scope.schedulerStartMinute, 0, 59, 2) && InRange(scope.schedulerStartSecond, 0, 59, 2)) ) {
                        this.scope.scheduler_startTime_error = true;
                        validity = false;
                    }
                    if (!this.scope.scheduler_form.schedulerName.$valid) {
                        // Make sure schedulerName requird error shows up
                        this.scope.scheduler_form.schedulerName.$dirty = true;
                        $('#schedulerName').addClass('ng-dirty');
                        validity = false;
                    }
                    if(this.scope.cleanupJob===true && !this.scope.scheduler_form.schedulerPurgeDays.$valid){
                        this.scope.scheduler_form.schedulerPurgeDays.$dirty = true;
                        $('#schedulerPurgeDays').addClass('ng-dirty');
                        validity = false;
                    }
                    if (this.scope.schedulerEnd.value === 'on') {
                        if (!/^\d{2}\/\d{2}\/\d{4}$/.test(this.scope.schedulerEndDt)) {
                            this.scope.scheduler_form.schedulerEndDt.$pristine = false;
                            this.scope.scheduler_form.schedulerEndDt.$dirty = true;
                            $('#schedulerEndDt').removeClass('ng-pristine').removeClass('ng-valid').removeClass('ng-valid-custom-error')
                                .addClass('ng-dirty').addClass('ng-invalid').addClass('ng-invalid-custom-error');
                            this.scope.scheduler_endDt_error = true;
                            validity = false;
                        }
                    }
                    if (this.scope.schedulerUTCTime) {
                        try {
                            startDt = new Date(this.scope.schedulerUTCTime);
                            if (!isNaN(startDt)) {
                                timeFuture = startDt.getTime();
                                now = new Date();
                                if (this.useTimezone) {
                                    dateStr = now.getFullYear() + '-' +
                                        $filter('schZeroPad')(now.getMonth() + 1, 2)+ '-' +
                                        $filter('schZeroPad')(now.getDate(),2) + 'T' +
                                        $filter('schZeroPad')(now.getHours(),2) + ':' +
                                        $filter('schZeroPad')(now.getMinutes(),2) + ':' +
                                        $filter('schZeroPad')(now.getSeconds(),2) + '.000Z';
                                    adjNow = $timezones.toUTC(dateStr, this.scope.schedulerTimeZone.name);   //Adjust to the selected TZ
                                    timeNow = adjNow.getTime();
                                }
                                else {
                                    timeNow = now.getTime();
                                }
                                if (this.requireFutureStartTime && timeNow >= timeFuture) {
                                    this.scope.startDateError("Start time must be in the future");
                                    validity = false;
                                }
                            }
                            else {
                                this.scope.startDateError("Invalid start time");
                                validity = false;
                            }
                        }
                        catch(e) {
                            this.scope.startDateError("Invalid start time");
                            validity = false;
                        }
                    }
                    else {
                        this.scope.startDateError("Provide a start time");
                        validity = false;
                    }

                    scope.schedulerIsValid = validity;
                    if (validity) {
                        this.setDetails();
                    }

                    return validity;
                };

                // Returns an rrule object
                this.getRRule = function() {
                    var options = this.getOptions();
                    return GetRule(options);
                };

                // Return object containing schedule name, string representation of rrule per iCalendar RFC,
                // and options used to create rrule
                this.getValue = function() {
                    var rule = this.getRRule(),
                        options = this.getOptions();
                    return {
                        name: scope.schedulerName,
                        rrule: rule.toString(),
                        options: options
                    };
                };

                this.setRRule = function(rule) {
                    this.clear();
                    return SetRule(rule, this.scope);
                };

                this.setName = function(name) {
                    this.scope.schedulerName = name;
                };

                // Read in the HTML partial, compile and inject it into the DOM.
                // Pass in the target element's id attribute value or an angular.element()
                // object.
                this.inject = function(element, showButtons) {
                    return Inject({ scope: this.scope, target: element, buttons: showButtons });
                };

                this.injectDetail = function(element, showRRule) {
                    return InjectDetail({ scope: this.scope, target: element, showRRule: showRRule });
                };

                // Clear the form, returning all elements to a default state
                this.clear = function() {
                    this.clearErrors();
                    if (this.scope.scheduler_form && this.scope.scheduler_form.schedulerName) {
                        this.scope.scheduler_form.schedulerName.$setPristine();
                    }
                    this.scope.setDefaults();
                };

                // Get the user's local timezone
                this.getUserTimezone = function() {
                    return $timezones.getLocal();
                };

                // futureStartTime setter/getter
                this.setRequireFutureStartTime = function(opt) {
                    this.requireFutureStartTime = opt;
                };

                this.getRequireFutureStartTime = function() {
                    return this.requireFutureStartTime;
                };

                this.setShowRRule = function(opt) {
                    scope.showRRule = opt;
                };
            };
            return new fn();
        };
    }])

    .factory('InRange', [ function() {
        return function(x, min, max, length) {
            var rx = new RegExp("\\d{1," + length + "}");
            if (!rx.test(x)) {
                return false;
            }
            if (x < min || x > max) {
                return false;
            }
            return true;
        };
    }])

    .factory('Inject', ['AngularScheduler.partials', '$compile', '$http', '$log', function(scheduler_partial, $compile, $http) {
        return function(params) {

            var scope = params.scope,
                target = params.target,
                buttons = params.buttons;

            if (scope.removeHtmlReady) {
                scope.removeHtmlReady();
            }
            scope.removeHtmlReady = scope.$on('htmlReady', function(e, data) {
                var element = (angular.isObject(target)) ? target : angular.element(document.getElementById(target));
                element.html(data);
                $compile(element)(scope);
                if (buttons) {
                    $('#scheduler-buttons').show();
                }
            });

            $http({ method: 'GET', url: scheduler_partial + 'angular-scheduler.html' })
                .success( function(data) {
                    scope.$emit('htmlReady', data);
                })
                .error( function(data, status) {
                    throw('Error reading ' + scheduler_partial + 'angular-scheduler.html. ' + status);
                    //$log.error('Error calling ' + scheduler_partial + '. ' + status);
                });
        };
    }])

    .factory('InjectDetail', ['AngularScheduler.partials', '$compile', '$http', '$log', function(scheduler_partial, $compile, $http) {
        return function(params) {

            var scope = params.scope,
                target = params.target,
                showRRule = params.showRRule;

            scope.showRRule = showRRule || false;

            if (scope.removeHtmlDetailReady) {
                scope.removeHtmlDetailReady();
            }
            scope.removeHtmlDetailReady = scope.$on('htmlDetailReady', function(e, data) {
                var element = (angular.isObject(target)) ? target : angular.element(document.getElementById(target));
                element.html(data);
                $compile(element)(scope);
            });

            $http({ method: 'GET', url: scheduler_partial + 'angular-scheduler-detail.html' })
                .success( function(data) {
                    scope.$emit('htmlDetailReady', data);
                })
                .error( function(data, status) {
                    throw('Error reading ' + scheduler_partial + 'angular-scheduler-detail.html. ' + status);
                    //$log.error('Error calling ' + scheduler_partial + '. ' + status);
                });
        };
    }])

    .factory('GetRule', ['$log', function($log) {
        return function(params) {
            // Convert user inputs to an rrule. Returns rrule object using https://github.com/jkbr/rrule
            // **list of 'valid values' found below in LoadLookupValues

            var startDate = params.startDate,  // date object or string in yyyy-MM-ddTHH:mm:ss.sssZ format
                frequency = params.frequency,  // string, optional, valid value from frequencyOptions
                interval = params.interval,    // integer, optional
                occurrenceCount = params.occurrenceCount,  //integer, optional
                endDate = params.endDate,      // date object or string in yyyy-MM-dd format, optional
                                               // ignored if occurrenceCount provided
                month = params.month,          // integer, optional, valid value from months
                monthDay = params.monthDay,    // integer, optional, between 1 and 31
                weekDays = params.weekDays,     // integer, optional, valid value from weekdays
                setOccurrence = params.setOccurrence, // integer, optional, valid value from occurrences
                options = {}, i;

            if (angular.isDate(startDate)) {
                options.dtstart = startDate;
            }
            else {
                try {
                    options.dtstart = new Date(startDate);
                }
                catch(e) {
                    $log.error('Date conversion failed. Attempted to convert ' + startDate + ' to Date. ' + e.message);
                }
            }

            if (frequency && frequency !== 'none') {
                options.freq = RRule[frequency.toUpperCase()];
                options.interval = interval;

                if (weekDays && typeof weekDays === 'string') {
                    options.byweekday = RRule[weekDays.toUpperCase()];
                }

                if (weekDays && angular.isArray(weekDays)) {
                    options.byweekday = [];
                    for (i=0; i < weekDays.length; i++) {
                        options.byweekday.push(RRule[weekDays[i].toUpperCase()]);
                    }
                }

                if (setOccurrence !== undefined && setOccurrence !== null) {
                    options.bysetpos = setOccurrence;
                }

                if (month) {
                    options.bymonth = month;
                }

                if (monthDay) {
                    options.bymonthday = monthDay;
                }

                if (occurrenceCount) {
                    options.count = occurrenceCount;
                }
                else if (endDate) {
                    if (angular.isDate(endDate)) {
                        options.until = endDate;
                    }
                    else {
                        try {
                            options.until = new Date(endDate);
                        }
                        catch(e) {
                            $log.error('Date conversion failed. Attempted to convert ' + endDate + ' to Date. ' + e.message);
                        }
                    }
                }
            }
            else {
                // We only want to run 1x
                options.freq = RRule.DAILY;
                options.interval = 1;
                options.count = 1;
            }
            return new RRule(options);
        };
    }])

    .factory('SetRule', ['AngularScheduler.useTimezone', '_', '$log', '$timezones', '$filter',
    function(useTimezone, _, $log, $timezones, $filter) {
        return function(rule, scope) {
            var set, result = '', i,
                setStartDate = false;

            // Search the set of RRule keys for a particular key, returning its value
            function getValue(set, key) {
                var pair = _.find(set, function(x) {
                    var k = x.split(/=/)[0].toUpperCase();
                    return (k === key);
                });
                if (pair) {
                    return pair.split(/=/)[1].toUpperCase();
                }
                return null;
            }

            function toWeekDays(days) {
                var darray = days.toLowerCase().split(/,/),
                    match = _.find(scope.weekdays, function(x) {
                        var warray = (angular.isArray(x.value)) ? x.value : [x.value],
                            diffA = _.difference(warray, darray),
                            diffB = _.difference(darray, warray);
                        return (diffA.length === 0 && diffB.length === 0);
                    });
                return match;
            }

            function setValue(pair, set) {
                var key = pair.split(/=/)[0].toUpperCase(),
                    value = pair.split(/=/)[1],
                    days, l, j, dt, month, day, timeString;

                if (key === 'NAME') {
                    //name is not actually part of RRule, but we can handle it just the same
                    scope.schedulerName = value;
                }

                if (key === 'FREQ') {
                    l = value.toLowerCase();
                    scope.schedulerFrequency = _.find(scope.frequencyOptions, function(opt) {
                        scope.schedulerIntervalLabel = opt.intervalLabel;
                        return opt.value === l;
                    });
                    if (!scope.schedulerFrequency || !scope.schedulerFrequency.name) {
                        result = 'FREQ not found in list of valid options';
                    }
                }
                if (key === 'INTERVAL') {
                    if (parseInt(value,10)) {
                        scope.schedulerInterval = parseInt(value,10);
                        scope.schedulerShowInterval = true;
                    }
                    else {
                        result = 'INTERVAL must contain an integer > 0';
                    }
                }
                if (key === 'BYDAY') {
                    if (getValue(set, 'FREQ') === 'WEEKLY') {
                        days = value.split(/,/);
                        scope.weekDays = [];
                        for (j=0; j < days.length; j++) {
                            if (_.contains(['SU','MO','TU','WE','TH','FR','SA'], days[j])) {
                                scope.weekDays.push(days[j].toLowerCase());
                                scope['weekDay' + days[j].toUpperCase() + 'Class'] = 'active'; //activate related button
                            }
                            else {
                                result = 'BYDAY contains unrecognized day value(s)';
                            }
                        }
                    }
                    else if (getValue(set, 'FREQ') === 'MONTHLY') {
                        scope.monthlyRepeatOption = 'other';
                        scope.monthlyWeekDay = toWeekDays(value);
                        if (!scope.monthlyWeekDay) {
                            result = 'BYDAY contains unrecognized day value(s)';
                        }
                    }
                    else {
                        scope.yearlyRepeatOption = 'other';
                        scope.yearlyWeekDay = toWeekDays(value);
                        if (!scope.yearlyWeekDay) {
                            result = 'BYDAY contains unrecognized day value(s)';
                        }
                    }
                }
                if (key === 'BYMONTHDAY') {
                    if (parseInt(value,10) && parseInt(value,10) > 0 && parseInt(value,10) < 32) {
                        scope.monthDay = parseInt(value,10);
                        scope.monhthlyRepeatOption = 'day';
                    }
                    else {
                        result = 'BYMONTHDAY must contain an integer between 1 and 31';
                    }
                }
                if (key === 'DTSTART') {
                    // The form has been reset to the local zone
                    setStartDate = true;
                    if (/\d{8}T\d{6}.*Z/.test(value)) {
                        // date may come in without separators. add them so new Date constructor will work
                        value = value.replace(/(\d{4})(\d{2})(\d{2}T)(\d{2})(\d{2})(\d{2}.*$)/,
                            function(match, p1, p2, p3, p4,p5,p6) {
                                return p1 + '-' + p2 + '-' + p3 + p4 + ':' + p5 + ':' + p6.substr(0,2) + 'Z';
                            });
                    }
                    if (useTimezone) {
                        dt = new Date(value); // date adjusted to local zone automatically
                        month = $filter('schZeroPad')(dt.getMonth() + 1, 2);
                        day = $filter('schZeroPad')(dt.getDate(), 2);
                        scope.schedulerStartDt = month + '/' + day + '/' + dt.getFullYear();
                        scope.schedulerStartHour = $filter('schZeroPad')(dt.getHours(),2);
                        scope.schedulerStartMinute = $filter('schZeroPad')(dt.getMinutes(),2);
                        scope.schedulerStartSecond = $filter('schZeroPad')(dt.getSeconds(),2);
                        scope.scheduleTimeChange();  // calc UTC
                    }
                    else {
                        // expects inbound dates to be in ISO format: 2014-04-02T00:00:00.000Z
                        scope.schedulerStartDt = value.replace(/T.*$/,'').replace(/(\d{4})-(\d{2})-(\d{2})/, function(match, p1, p2, p3) {
                                return p2 + '/' + p3 + '/' + p1;
                            });
                        timeString = value.replace(/^.*T/,'');
                        scope.schedulerStartHour = $filter('schZeroPad')(timeString.substr(0,2),2);
                        scope.schedulerStartMinute = $filter('schZeroPad')(timeString.substr(3,2),2);
                        scope.schedulerStartSecond  = $filter('schZeroPad')(timeString.substr(6,2),2);
                    }
                    scope.scheduleTimeChange();
                }
                if (key === 'BYSETPOS') {
                    if (getValue(set, 'FREQ') === 'YEARLY') {
                        scope.yearlRepeatOption = 'other';
                        scope.yearlyOccurrence = _.find(scope.occurrences, function(x) {
                            return (x.value === parseInt(value,10));
                        });
                        if (!scope.yearlyOccurrence || !scope.yearlyOccurrence.name) {
                            result = 'BYSETPOS was not in the set of 1,2,3,4,-1';
                        }
                    }
                    else {
                        scope.monthlyOccurrence = _.find(scope.occurrences, function(x) {
                            return (x.value === parseInt(value,10));
                        });
                        if (!scope.monthlyOccurrence || !scope.monthlyOccurrence.name) {
                            result = 'BYSETPOS was not in the set of 1,2,3,4,-1';
                        }
                    }
                }

                if (key === 'COUNT') {
                    if (parseInt(value,10)) {
                        scope.schedulerEnd = scope.endOptions[1];
                        scope.schedulerOccurrenceCount = parseInt(value,10);
                    }
                    else {
                        result = "COUNT must be a valid integer > 0";
                    }
                }

                if (key === 'UNTIL') {
                    if (/\d{8}T\d{6}.*Z/.test(value)) {
                        // date may come in without separators. add them so new Date constructor will work
                        value = value.replace(/(\d{4})(\d{2})(\d{2}T)(\d{2})(\d{2})(\d{2}.*$)/,
                            function(match, p1, p2, p3, p4,p5,p6) {
                                return p1 + '-' + p2 + '-' + p3 + p4 + ':' + p5 + ':' + p6.substr(0,2) + 'Z';
                            });
                    }
                    scope.schedulerEnd = scope.endOptions[2];
                    if (useTimezone) {
                        dt = new Date(value); // date adjusted to local zone automatically
                        month = $filter('schZeroPad')(dt.getMonth() + 1, 2);
                        day = $filter('schZeroPad')(dt.getDate(), 2);
                        scope.schedulerEndDt = month + '/' + day + '/' + dt.getFullYear();
                    }
                    else {
                        scope.schedulerEndDt = value.replace(/T.*$/,'').replace(/(\d{4})-(\d{2})-(\d{2})/, function(match, p1, p2, p3) {
                            return p2 + '/' + p3 + '/' + p1;
                        });
                    }
                }

                if (key === 'BYMONTH') {
                    if (getValue(set, 'FREQ') === 'YEARLY' && getValue(set, 'BYDAY')) {
                        scope.yearlRepeatOption = 'other';
                        scope.yearlyOtherMonth =  _.find(scope.months, function(x) {
                            return x.value === parseInt(value,10);
                        });
                        if (!scope.yearlyOtherMonth || !scope.yearlyOtherMonth.name) {
                            result = 'BYMONTH must be an integer between 1 and 12';
                        }
                    }
                    else {
                        scope.yearlyOption = 'month';
                        scope.yearlyMonth = _.find(scope.months, function(x) {
                            return x.value === parseInt(value,10);
                        });
                        if (!scope.yearlyMonth || !scope.yearlyMonth.name) {
                            result = 'BYMONTH must be an integer between 1 and 12';
                        }
                    }
                }

                if (key === 'BYMONTHDAY') {
                    if (parseInt(value,10)) {
                        scope.yearlyMonthDay = parseInt(value,10);
                    }
                    else {
                        result = 'BYMONTHDAY must be an integer between 1 and 31';
                    }
                }
            }

            function isValid() {
                // Check what was put into scope vars, and see if anything is
                // missing or not quite right.
                if (scope.schedulerFrequency.name === 'weekly' && scope.weekDays.length === 0) {
                    result = 'Frequency is weekly, but BYDAYS value is missing.';
                }
                if (!setStartDate) {
                    result = 'Warning: start date was not provided';
                }
            }

            if (rule) {
                set = rule.split(/;/);
                if (angular.isArray(set)) {
                    for (i=0; i < set.length; i++) {
                        setValue(set[i], set);
                        if (result) {
                            break;
                        }
                    }
                    if (!result) {
                        isValid();
                    }
                }
                else {
                    result = 'No rule entered. Provide a valid RRule string.';
                }
            }
            else {
                result = 'No rule entered. Provide a valid RRule string.';
            }
            if (result) {
                $log.error(result);
            }
            return result;
        };
    }])

    .factory('SetDefaults', ['$filter', function($filter) {
        return function(scope) {
            // Set default values
            var defaultDate = new Date(),
                defaultMonth = $filter('schZeroPad')(defaultDate.getMonth() + 1, 2),
                defaultDay = $filter('schZeroPad')(defaultDate.getDate(), 2),
                defaultDateStr = defaultMonth + '/' + defaultDay + '/' + defaultDate.getFullYear();
            scope.schedulerName = '';
            scope.schedulerPurgeDays = 30;
            scope.weekDays = [];
            scope.schedulerStartHour = '00';
            scope.schedulerStartMinute = '00';
            scope.schedulerStartSecond = '00';
            scope.schedulerStartDt = defaultDateStr;
            scope.schedulerFrequency = scope.frequencyOptions[0];
            scope.schedulerShowEvery = false;
            scope.schedulerEnd = scope.endOptions[0];
            scope.schedulerInterval = 1;
            scope.schedulerOccurrenceCount = 1;
            scope.monthlyRepeatOption = 'day';
            scope.monthDay = 1;
            scope.monthlyOccurrence = scope.occurrences[0];
            scope.monthlyWeekDay = scope.weekdays[0];
            scope.yearlyRepeatOption = 'month';
            scope.yearlyMonth = scope.months[0];
            scope.yearlyMonthDay = 1;
            scope.yearlyWeekDay = scope.weekdays[0];
            scope.yearlyOtherMonth = scope.months[0];
            scope.yearlyOccurrence = scope.occurrences[0];
            scope.weekDayMOClass = '';
            scope.weekDayTUClass = '';
            scope.weekDayWEClass = '';
            scope.weekDayTHClass = '';
            scope.weekDayFRClass = '';
            scope.weekDaySAClass = '';
            scope.weekDaySUClass = '';

            //Detail view
            scope.schedulerIsValid = false;
            scope.rrule_nlp_description = '';
            scope.rrule = '';
            scope.dateChoice = 'utc';
            scope.occurrence_list = [];
        };
    }])

    .factory('LoadLookupValues', [ function() {
        return function(scope) {

            scope.frequencyOptions = [
                { name: 'None (run once)', value: 'none', intervalLabel: '' },
                { name: 'Minute', value: 'minutely', intervalLabel: 'minutes' },
                { name: 'Hour', value: 'hourly', intervalLabel: 'hours' },
                { name: 'Day', value: 'daily', intervalLabel: 'days' },
                { name: 'Week', value: 'weekly', intervalLabel: 'weeks' },
                { name: 'Month', value: 'monthly', intervalLabel: 'months' },
                { name: 'Year', value: 'yearly', intervalLabel: 'years' }
            ];

            scope.endOptions = [
                { name: 'Never', value: 'never' },
                { name: 'After', value: 'after' },
                { name: 'On Date', value: 'on' }
            ];

            scope.occurrences = [
                { name: 'first', value: 1 },
                { name: 'second', value: 2 },
                { name: 'third', value: 3 },
                { name: 'fourth', value: 4 },
                { name: 'last', value: -1 }
            ];

            scope.weekdays = [
                { name: 'Sunday', value: 'su' },
                { name: 'Monday', value: 'mo' },
                { name: 'Tueday', value: 'tu' },
                { name: 'Wednesday', value: 'we' },
                { name: 'Thursday', value: 'th' },
                { name: 'Friday', value: 'fr' },
                { name: 'Saturday', value: 'sa' },
                { name: 'Day', value: ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su'] },
                { name: 'Weekday', value: ['mo', 'tu', 'we', 'th', 'fr'] },
                { name: 'Weekend day', value: ['sa', 'su'] }
            ];

            scope.months = [
                { name: 'January', value: 1 },
                { name: 'February', value: 2 },
                { name: 'March', value: 3 },
                { name: 'April', value: 4 },
                { name: 'May', value: 5 },
                { name: 'June', value: 6 },
                { name: 'July', value: 7 },
                { name: 'August', value: 8 },
                { name: 'September', value: 9 },
                { name: 'October', value: 10 },
                { name: 'November', value: 11 },
                { name: 'December', value: 12 }
            ];

        };
    }])

    // $filter('schZeroPad')(n, pad) -- or -- {{ n | afZeroPad:pad }}
    .filter('schZeroPad', [ function() {
        return function (n, pad) {
            var str = (Math.pow(10,pad) + '').replace(/^1/,'') + (n + '').trim();
            return str.substr(str.length - pad);
        };
    }])

    // $filter('schdateStrFix')(s)  where s is a date string in ISO format: yyyy-mm-ddTHH:MM:SS.sssZ. Returns string in format: mm/dd/yyyy HH:MM:SS UTC
    .filter('schDateStrFix', [ function() {
        return function(dateStr) {
            return dateStr.replace(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2}).*Z/, function(match, yy, mm, dd, hh, mi, ss) {
                return mm + '/' + dd + '/' + yy + ' ' + hh + ':' + mi + ':' + ss + ' UTC';
            });
        };
    }])

    .directive('schTooltip', [ function() {
        return {
            link: function(scope, element, attrs) {
                var placement = (attrs.placement) ? attrs.placement : 'top';
                $(element).tooltip({
                    html: true,
                    placement: placement,
                    title: attrs.afTooltip,
                    trigger: 'hover',
                    container: 'body'
                });
            }
        };
    }])

    .directive('schDatePicker', [ function() {
        return {
            require: 'ngModel',
            link: function(scope, element, attrs) {
                    var options = {},
                        variable = attrs.ngModel,
                        defaultDate = new Date();
                    options.dateFormat = attrs.dateFormat || 'mm/dd/yy';
                    options.defaultDate = scope[variable];
                    options.minDate = (attrs.minToday) ? defaultDate : null;
                    options.maxDate = (attrs.maxDate) ? new Date(attrs('maxDate')) : null;
                    options.changeMonth = (attrs.changeMonth === "false")  ? false : true;
                    options.changeYear = (attrs.changeYear === "false") ? false : true;
                    options.beforeShow = function() {
                        setTimeout(function(){
                            $('.ui-datepicker').css('z-index', 9999);
                        }, 100);
                    };
                    $(element).datepicker(options);
                }
        };
    }])

     // Custom directives
    .directive('schSpinner', ['$filter', function($filter) {
        return {
            require: 'ngModel',
            link: function(scope, element, attr, ctrl) {
                // Add jquerui spinner to 'spinner' type input
                var form = attr.schSpinner,
                    zeroPad = attr.zeroPad,
                    min = attr.min || 1,
                    max = attr.max || 999;
                $(element).spinner({
                    min: min,
                    max: max,
                    stop: function() {
                        //update the model immediately
                        setTimeout(function() {
                            scope.$apply(function() {
                                if (zeroPad) {
                                    scope[attr.ngModel] = $filter('schZeroPad')($(element).spinner('value'),zeroPad);
                                }
                                else {
                                    scope[attr.ngModel] = $(element).spinner('value');
                                }
                                if (attr.ngChange) {
                                    scope.$eval(attr.ngChange);
                                }
                            });
                        }, 100);
                    },
                    spin: function() {
                        scope[form].$setDirty();
                        ctrl.$dirty = true;
                        ctrl.$pristine = false;
                        if (!scope.$$phase) {
                            scope.$digest();
                        }
                    }
                });

                $(element).on("click", function () {
                    $(element).select();
                });
            }
        };
    }]);
