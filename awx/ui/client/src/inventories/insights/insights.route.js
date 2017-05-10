import {templateUrl} from '../../shared/template-url/template-url.factory';
import { N_ } from '../../i18n';

export default {
    url: '/insights',
    ncyBreadcrumb: {
        label: N_("INSIGHTS")
    },
    views: {
        'related': {
            controller: 'InsightsController',
            templateUrl: templateUrl('inventories/insights/insights')
        }
    },
    resolve: {
        Facts: ['$stateParams', 'GetBasePath', 'Rest',
            function($stateParams, GetBasePath, Rest) {
                let ansibleFactsUrl = GetBasePath('hosts') + $stateParams.host_id + '/ansible_facts';
                Rest.setUrl(ansibleFactsUrl);
                return Rest.get()
                    .success(function(data) {
                        return data;
                    });
            }
        ]
    }
};
