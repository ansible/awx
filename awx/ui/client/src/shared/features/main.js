/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
import awFeatureDirective from './features.directive';
import FeaturesService from './features.service';

export default
    angular.module('features', [])
        .directive('awFeature', awFeatureDirective)
        .service('FeaturesService', FeaturesService);
