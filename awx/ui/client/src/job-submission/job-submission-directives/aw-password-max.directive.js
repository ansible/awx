/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/* jshint unused: vars */

export default
    [   'Empty',
        function(Empty) {
            return {
                restrict: 'A',
                require: 'ngModel',
                link: function(scope, elem, attr, ctrl) {
                    ctrl.$parsers.unshift(function(viewValue) {
                        var max = (attr.awPasswordMax) ? scope.$eval(attr.awPasswordMax) : Infinity;
                        if (!Empty(max) && !Empty(viewValue) && viewValue.length > max && viewValue !== '$encrypted$') {
                            ctrl.$setValidity('awPasswordMax', false);
                            return viewValue;
                        } else {
                            ctrl.$setValidity('awPasswordMax', true);
                            return viewValue;
                        }
                    });
                }
            };
        }
    ];
