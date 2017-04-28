/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
     [   'Empty',
         function(Empty) {
             return {
                 restrict: 'A',
                 require: 'ngModel',
                 link: function(scope, elem, attr, ctrl) {
                     ctrl.$parsers.unshift(function(viewValue) {
                         var min = (attr.awPasswordMin) ? scope.$eval(attr.awPasswordMin) : -Infinity;
                         if (!Empty(min) && !Empty(viewValue) && viewValue.length < min && viewValue !== '$encrypted$') {
                             ctrl.$setValidity('awPasswordMin', false);
                             return viewValue;
                         } else {
                             ctrl.$setValidity('awPasswordMin', true);
                             return viewValue;
                         }
                     });
                 }
             };
         }
     ];
