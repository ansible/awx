import {templateUrl} from '../shared/template-url/template-url.factory';

export default {
    name: 'setup',
    route: '/setup',
    ncyBreadcrumb: {
        label: "SETTINGS"
    },
    templateUrl: templateUrl('setup-menu/setup-menu'),
    resolve: {
        org_admin:
            ['$rootScope', 'ProcessErrors', 'Rest',
            function($rootScope, ProcessErrors, Rest){
            $rootScope.loginConfig.promise.then(function () {
                if($rootScope.current_user.related.admin_of_organizations){
                $rootScope.orgAdmin = false;
                if ($rootScope.current_user.is_superuser) {
                    $rootScope.orgAdmin = true;
                } else {
                    Rest.setUrl(`/api/v1/users/${$rootScope.current_user.id}/admin_of_organizations`);
                    Rest.get()
                        .success(function(data) {
                            $rootScope.orgAdmin = (data.count) ? true : false;
                        }).error(function (data, status) {
                            ProcessErrors($rootScope, data, status, null, { hdr: 'Error!', msg: 'Failed to find if users is admin of org' + status });
                        });
                }
            }
            else{
                return;
            }
        });
        }]
    }
};
