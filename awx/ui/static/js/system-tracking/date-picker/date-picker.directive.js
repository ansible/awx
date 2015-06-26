/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */

export default
    [   'moment',
        function(moment) {
            return {
                restrict: 'E',
                scope: {
                    date: '=',
                    minDate: '=',
                    autoUpdate: '=?',
                    inputClass: '&'
                },
                templateUrl: '/static/js/system-tracking/date-picker/date-picker.partial.html',
                link: function(scope, element, attrs) {

                    // We need to make sure this _never_ recurses, which sometimes happens
                    // with two-way binding.
                    var mustUpdateValue = true;
                    scope.autoUpdate = scope.autoUpdate === false ? false : true;

                    scope.$watch('minDate', function(newValue) {
                        if (newValue) {

                            if (scope.autoUpdate && scope.date.isBefore(newValue)) {
                                scope.date = newValue;
                            }

                            $('.date', element).systemTrackingDP('setStartDate', newValue.toDate());
                        }
                    });

                    scope.$watch('date', function(newValue) {
                        if (newValue) {
                            mustUpdateValue = false;
                            scope.dateValue = newValue.format('L');
                        }
                    }, true);

                    scope.$watch('dateValue', function(newValue) {
                        var newDate = moment(newValue, ['L'], moment.locale());

                        if (newValue && !newDate.isValid()) {
                            scope.error = "That is not a valid date.";
                        } else if (newValue) {
                            scope.date = newDate;
                        }
                        mustUpdateValue = true;
                    });

                    var localeData =
                        moment.localeData();
                    var dateFormat = momentFormatToDPFormat(localeData._longDateFormat.L);
                    var localeKey = momentLocaleToDPLocale(moment.locale());

                    element.find(".DatePicker").addClass("input-prepend date");
                    element.find(".DatePicker").find(".DatePicker-icon").addClass("add-on");
                    $(".date").systemTrackingDP({
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
