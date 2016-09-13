/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    angular.module('rbacUiControl', [])
        .service('rbacUiControlService', ['$q', 'GetBasePath', 'Rest', function($q, GetBasePath, Rest){
            this.canAdd = function(apiPath) {
                var canAddVal = $q.defer();

                if (apiPath.indexOf("api/v1") > -1) {
                    Rest.setUrl(apiPath);
                } else {
                    Rest.setUrl(GetBasePath(apiPath));
                }

                Rest.options()
                    .success(function(data) {
                        if (data.actions.POST) {
                            canAddVal.resolve(true);
                        } else {
                            canAddVal.reject(false);
                        }
                    });

                return canAddVal.promise;
            };
        }]);
