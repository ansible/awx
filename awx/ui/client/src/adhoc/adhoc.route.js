/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    route: '/adhoc',
    name: 'inventoryManage.adhoc',
    templateUrl: templateUrl('adhoc/adhoc'),
    controller: 'adhocController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }]
    }
};
