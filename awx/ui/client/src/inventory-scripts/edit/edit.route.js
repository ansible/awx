/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'inventoryScriptsEdit',
    route: '/inventory_scripts/:inventory_script',
    templateUrl: templateUrl('inventory-scripts/edit/edit'),
    controller: 'inventoryScriptsEditController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        inventory_script:
        [   '$state',
            '$stateParams',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($state, $stateParams, $q, rest, getBasePath, ProcessErrors) {
                // if ($stateParams.inventory_script) {
                //     $stateParams.inventory_script = JSON.parse($stateParams.inventory_script);
                //     return $q.when($stateParams.inventory_script);
                // }

                var inventoryScriptId = $stateParams.inventory_script;

                var url = getBasePath('inventory_scripts') + inventoryScriptId + '/';
                rest.setUrl(url);
                return rest.get()
                    .then(function(data) {
                        return data.data;
                    }).catch(function (response) {
                    ProcessErrors(null, response.data, response.status, null, {
                        hdr: 'Error!',
                        msg: 'Failed to get inventory script info. GET returned status: ' +
                        response.status
                    });
                });
            }
        ]
    }
};
