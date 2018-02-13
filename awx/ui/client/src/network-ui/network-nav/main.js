import NetworkingController from './network.nav.controller';
import NetworkingStrings from './network.nav.strings';

const MODULE_NAME = 'at.features.networking';

const networkNavTemplate = require('~network-ui/network-nav/network.nav.view.html');

function NetworkingResolve ($stateParams, resourceData) {
    const resolve = {
        inventory: {
            id: $stateParams.inventory_id,
            name: $stateParams.inventory_name
        }
    };
    if (!resolve.inventory.name) {
        resolve.inventory.name = resourceData.data.name;
    }
    return resolve;
}

NetworkingResolve.$inject = [
    '$stateParams',
    'resourceData'
];
function NetworkingRun ($stateExtender, strings) {
    $stateExtender.addState({
        name: 'inventories.edit.networking',
        route: '/networking',
        ncyBreadcrumb: {
            label: strings.get('state.BREADCRUMB_LABEL')
        },
        views: {
            'networking@': {
                templateUrl: networkNavTemplate,
                controller: NetworkingController,
                controllerAs: 'vm'
            }
        },
        resolve: {
            resolvedModels: NetworkingResolve
        }
    });
}

NetworkingRun.$inject = [
    '$stateExtender',
    'NetworkingStrings'
];

angular
    .module(MODULE_NAME, [])
    .service('NetworkingStrings', NetworkingStrings)
    .run(NetworkingRun);

export default MODULE_NAME;
