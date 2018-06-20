import { N_ } from '../i18n';
import NetworkingController from './network-nav/network.nav.controller';

const networkNavTemplate = require('~network-ui/network-nav/network.nav.view.html');

export default {
    name: 'inventories.edit.networking',
    route: '/networking',
    ncyBreadcrumb: {
        label: N_("INVENTORIES")
    },
    views: {
        'networking@': {
            templateUrl: networkNavTemplate,
            controller: NetworkingController,
            controllerAs: 'vm'
        }
    },
    resolve: {
        inventory: ['$stateParams', 'resourceData', 
            function($stateParams, resourceData){
                let inventory = {
                    name: $stateParams.inventory_name || resourceData.data.name,
                    id: $stateParams.inventory_id || $stateParams.smartinventory_id
                };
                return inventory;
        }],
        canEdit: ['$stateParams', 'resourceData', 
            function($stateParams, resourceData){
                return resourceData.data.summary_fields.user_capabilities.edit;
            }
        ]
    }
};