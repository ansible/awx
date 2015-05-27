/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /* jshint unused: vars */

import controller from './breadcrumbs.controller';
import 'tower/shared/generator-helpers';

export default function() {

    return {
        restrict: 'E',
        controller: controller,
        transclude: true,
        templateUrl: '/static/js/shared/breadcrumbs/breadcrumbs.partial.html',
        scope: {
        },
        link: function(scope, element, attrs, controller) {
            // make breadcrumbs hidden until the current
            // breadcrumb has a title; this avoids
            // ugly rendering when an object's title
            // is fetched via ajax
            //
            controller.setHidden();

            scope.$watch('isHidden', function(value) {
                if (value) {
                    element.hide();
                } else {
                    element.show();
                }
            });
        }
    };
}
