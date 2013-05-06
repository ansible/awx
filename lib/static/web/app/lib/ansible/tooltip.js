/************************************
 * Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *
 *  tooltip.js
 *  
 *  Custom directive to enable TB tooltips. To add a tooltip to an element, include the following directive in
 *  the element's attributes:
 *
 *     aw-tool-tip="<< tooltip text here >>"
 *
 *  Include the standard TB data-XXX attributes to controll a tooltip's appearance.  We will default placement
 *  to the left and delay to 2 seconds.
 *
 */ 
angular.module('AWToolTip', [])
   .directive('awToolTip', function() {
       return function(scope, element, attrs) {
           var delay = (attrs.delay != undefined && attrs.delay != null) ? attrs.delay : $AnsibleConfig.tooltip_delay;
           var placement = (attrs.placement != undefined && attrs.placement != null) ? attrs.placement : 'left';
           $(element).tooltip({ placement: placement, delay: delay, title: attrs.awToolTip });
       }
   });