import NetworkingController from './networking.controller';
import NetworkingStrings from './networking.strings';

const MODULE_NAME = 'at.features.networking';

const networkingTemplate = require('~features/networking/networking.view.html');

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
                templateUrl: networkingTemplate,
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
