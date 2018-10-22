/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */

export default
    [   'moment',
        'templateUrl',
        function(moment, templateUrl) {
            require('bootstrap-datepicker');
            return {
                restrict: 'E',
                scope: {
                    date: '=',
                    minDate: '=',
                    autoUpdate: '=?',
                    inputClass: '&',
                    disabled: '=?'
                },
                templateUrl: templateUrl('scheduler/schedulerDatePicker'),
                link: function(scope, element, attrs) {
                    var lang = window.navigator.languages ?
                        window.navigator.languages[0] :
                            (window.navigator.language ||
                                window.navigator.userLanguage);
                    moment.locale(lang);
                    // We need to make sure this _never_ recurses, which sometimes happens
                    // with two-way binding.
                    var mustUpdateValue = true;
                    scope.autoUpdate = scope.autoUpdate === false ? false : true;

                    // convert the passed current date into the correct moment locale
                    scope.$watch('date', function(newValue) {
                        if (newValue) {
                            mustUpdateValue = false;
                            scope.dateValueMoment = moment(newValue, ['MM/DD/YYYY'], moment.locale());
                            scope.dateValue = scope.dateValueMoment.format('L');
                            element.find(".DatePicker").datepicker('update', scope.dateValue);
                        }
                    }, true);

                    // as the date picker value changes, convert back to
                    // the english date to pass back into the scheduler lib
                    scope.$watch('dateValue', function(newValue) {
                        scope.dateValueMoment = moment(newValue, ['L'], moment.locale());
                        scope.date = scope.dateValueMoment.locale('en').format('L');
                        mustUpdateValue = true;
                    });

                    var localeData =
                        moment.localeData();
                    var dateFormat = momentFormatToDPFormat(localeData._longDateFormat.L);
                    var localeKey = momentLocaleToDPLocale(moment.locale());

                    element.find(".DatePicker").addClass("input-prepend date");
                    element.find(".DatePicker").find(".DatePicker-icon").addClass("add-on");
                    element.find(".DatePicker").datepicker({
                        autoclose: true,
                        language: localeKey,
                        format: dateFormat
                    });

                    function momentLocaleToDPLocale(localeKey) {
                        var parts = localeKey.split('-');

                        if (parts.length === 2) {
                            var lastPart = parts[1].toUpperCase();
                            return [parts[0], lastPart].join('-');
                        } else {
                            return localeKey;
                        }

                    }

                    function momentFormatToDPFormat(momentFormat) {
                        var resultFormat = momentFormat;

                        function lowerCase(str) {
                            return str.toLowerCase();
                        }

                        resultFormat = resultFormat.replace(/D{1,2}/, lowerCase);

                        if (/MMM/.test(resultFormat)) {
                            resultFormat = resultFormat.replace('MMM', 'M');
                        } else {
                            resultFormat = resultFormat.replace(/M{1,2}/, 'm');
                        }

                        resultFormat = resultFormat.replace(/Y{2,4}/, lowerCase);

                        return resultFormat;
                    }
                }
            };
        }
    ];
