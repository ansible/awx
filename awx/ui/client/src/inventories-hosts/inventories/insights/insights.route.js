import {templateUrl} from '../../../shared/template-url/template-url.factory';
import { N_ } from '../../../i18n';

export default {
    url: '/insights',
    ncyBreadcrumb: {
        label: N_("INSIGHTS")
    },
    views: {
        'related': {
            controller: 'InsightsController',
            templateUrl: templateUrl('inventories-hosts/inventories/insights/insights')
        }
    },
    resolve: {
        InsightsData: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors',
            (Rest, $stateParams, GetBasePath, ProcessErrors) => {
                var path = `${GetBasePath('hosts')}${$stateParams.host_id}/insights`;
                Rest.setUrl(path);
                return Rest.get()
                    .then(function(data) {
                        return (data.data.insights_content);
                    }).catch(function(response) {
                        ProcessErrors(null, response.data, response.status, null, {
                            hdr: 'Error!',
                            msg: 'Failed to get insights info. GET returned status: ' +
                                response.status
                        });
                    });
            }
        ],
        InventoryData: ['Rest', '$stateParams', 'GetBasePath', 'ProcessErrors', 'resourceData',
            (Rest, $stateParams, GetBasePath, ProcessErrors, resourceData) => {
                if(resourceData.data.type === "host"){
                    var path = `${GetBasePath('inventory')}${resourceData.data.inventory}`;
                    Rest.setUrl(path);
                    return Rest.get()
                        .then(function(data) {
                            return (data.data);
                        }).catch(function(response) {
                            ProcessErrors(null, response.data, response.status, null, {
                                hdr: 'Error!',
                                msg: 'Failed to get insights info. GET returned status: ' +
                                    response.status
                            });
                        });
                }
                else if(resourceData.data.type === 'inventory'){
                    return resourceData.data;
                }
            }
        ]
    }
};
