/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import {templateUrl} from '../../shared/template-url/template-url.factory';

export default {
    name: 'inventoryScripts.edit',
    route: '/:inventory_script_id',
    templateUrl: templateUrl('inventory-scripts/edit/edit'),
    controller: 'inventoryScriptsEditController',
    params: {inventory_script: null},
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
                if ($stateParams.inventory_script) {
                    return $q.when($stateParams.inventory_script);
                }

                var inventoryScriptId = $stateParams.inventory_script_id;

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
