/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
/**
 *  @ngdoc overview
 *  @name features
 *  @scope
 *  @description enables/disables features based on license
 *
 *  @ngdoc directive
 *  @name features.directive:awFeature
 *  @description The aw-feature directive works by taking in a string
 *  that maps to a license feature, and removes that feature from the
 *  DOM if it is a feature not supported by the user's license.
 *  For example, adding `aw-feature="system-tracking"` will enable or disable
 *  the system tracking button based on the license configuration on the
 *  /config endpoint.
 *
 *
*/
import featureController from './features.controller';

export default [  function() {
    return {
        restrict: 'A',
        controller: featureController,
        link: function (scope, element, attrs, controller){
            if(attrs.awFeature.length > 0){
                if(!controller.isFeatureEnabled(attrs.awFeature)){
                    element.remove();
                }
            }
        }

    };
}];
