/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default {
    name: 'inventoryScriptsEdit',
    route: '/inventory_scripts/:inventory_script',
    templateUrl: '/static/js/inventory-scripts/edit/edit.partial.html',
    controller: 'editController',
    resolve: {
        features: ['FeaturesService', function(FeaturesService) {
            return FeaturesService.get();
        }],
        inventory_script:
        [   '$route',
            '$q',
            'Rest',
            'GetBasePath',
            'ProcessErrors',
            function($route, $q, rest, getBasePath, ProcessErrors) {
                if ($route.current.hasModelKey('inventory_script')) {
                    return $q.when($route.current.params.model.inventory_script);
                }

                var inventoryScriptId = $route.current.params.inventory_script;

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
        ],
    }
};
