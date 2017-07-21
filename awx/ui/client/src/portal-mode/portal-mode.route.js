import { templateUrl } from '../shared/template-url/template-url.factory';
import { PortalModeJobTemplatesController } from './portal-mode-job-templates.controller';
import { N_ } from '../i18n';

// Using multiple named views requires a parent layout
// https://github.com/angular-ui/ui-router/wiki/Multiple-Named-Views
export default {
    name: 'portalMode',
    url: '/portal?{job_template_search:queryset}',
    abstract: true,
    ncyBreadcrumb: {
        label: N_('MY VIEW')
    },
    params: {
        job_template_search: {
            value: {
                page_size: '20',
                order_by: 'name'
            },
            dynamic: true
        }
    },
    data: {
        socket: {
            "groups": {
                "jobs": ["status_changed"]
            }
        }
    },
    views: {
        '@': {
            templateUrl: templateUrl('portal-mode/portal-mode-layout'),
            controller: ['$scope', '$state',
                function($scope, $state) {

                    $scope.filterUser = function() {
                        $state.go('portalMode.myJobs');
                    };

                    $scope.filterAll = function() {
                        $state.go('portalMode.allJobs');
                    };
                }
            ]
        },
        // named ui-views inside the above
        'job-templates@portalMode': {
            templateProvider: function(PortalJobTemplateList, generateList) {
                let html = generateList.build({
                    list: PortalJobTemplateList,
                    mode: 'edit'
                });
                return html;
            },
            controller: PortalModeJobTemplatesController
        }
    },
    resolve: {
        job_templatesDataset: ['PortalJobTemplateList', 'QuerySet', '$stateParams', 'GetBasePath',
            function(list, qs, $stateParams, GetBasePath) {
                let path = GetBasePath(list.basePath) || GetBasePath(list.name);
                return qs.search(path, $stateParams[`${list.iterator}_search`]);
            }
        ]
    }
};
