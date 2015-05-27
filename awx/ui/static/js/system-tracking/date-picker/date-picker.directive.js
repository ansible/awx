/* jshint unused: vars */

export default
    [   '$rootScope',
        function() {
            return {
                restrict: 'E',
                scope: {
                    date: '='
                },
                templateUrl: '/static/js/system-tracking/date-picker/date-picker.partial.html',
                link: function(scope, element, attrs) {

                    // We need to make sure this _never_ recurses, which sometimes happens
                    // with two-way binding.
                    var mustUpdateValue = true;

                    scope.$watch('date', function(newValue) {
                        if (newValue) {
                            mustUpdateValue = false;
                            scope.dateValue = newValue.format('L');
                        }
                    }, true);

                    scope.$watch('dateValue', function(newValue) {
                        var newDate = moment(newValue);

                        if (newValue && !newDate.isValid()) {
                            scope.error = "That is not a valid date.";
                        } else if (newValue) {
                            scope.date = newDate;
                        }
                        mustUpdateValue = true;
                    });

                    element.find(".DatePicker").addClass("input-prepend date");
                    element.find(".DatePicker").find(".DatePicker-icon").addClass("add-on");
                    $(".date").systemTrackingDP({
                        autoclose: true
                    });
                }
            };
        }
    ];
