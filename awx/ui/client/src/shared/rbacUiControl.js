/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('rbacUiControl', [])
        .service('rbacUiControlService', ['$q', 'GetBasePath', 'Rest', 'Wait', function($q, GetBasePath, Rest, Wait){
            this.canAdd = function(apiPath) {
                var canAddVal = $q.defer();

                if (/api\/v[0-9]+\//.test(apiPath)) {
                    Rest.setUrl(apiPath);
                } else {
                    Rest.setUrl(GetBasePath(apiPath));
                }

                Wait("start");
                Rest.options()
                    .success(function(data) {
                        if (data.actions.POST) {
                            canAddVal.resolve({canAdd: true, options: data});
                        } else {
                            canAddVal.reject(false);
                        }
                        Wait("stop");
                    });

                return canAddVal.promise;
            };
        }]);
