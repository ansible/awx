/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobSubCredListController from './job-sub-cred-list.controller';

export default [ 'templateUrl', 'QuerySet', 'GetBasePath', 'generateList', '$compile', 'CredentialList',
    function(templateUrl, qs, GetBasePath, GenerateList, $compile, CredentialList) {
    return {
        scope: {},
        templateUrl: templateUrl('job-submission/lists/credential/job-sub-cred-list'),
        controller: jobSubCredListController,
        restrict: 'E',
        link: function(scope) {
            scope.credential_default_params = {
                order_by: 'name',
                page_size: 5,
                kind: 'ssh'
            };

            scope.credential_queryset = {
                order_by: 'name',
                page_size: 5,
                kind: 'ssh'
            };

            // Fire off the initial search
            qs.search(GetBasePath('credentials'), scope.credential_default_params)
                .then(function(res) {
                    scope.credential_dataset = res.data;
                    scope.credentials = scope.credential_dataset.results;

                    var credList = _.cloneDeep(CredentialList);
                    let html = GenerateList.build({
                        list: credList,
                        input_type: 'radio',
                        mode: 'lookup'
                    });

                    scope.list = credList;

                    $('#job-submission-credential-lookup').append($compile(html)(scope));

                    scope.$watchCollection('credentials', function () {
                        if(scope.selected_credential) {
                            // Loop across the inventories and see if one of them should be "checked"
                            scope.credentials.forEach(function(row, i) {
                                if (row.id === scope.selected_credential.id) {
                                    scope.credentials[i].checked = 1;
                                }
                                else {
                                    scope.credentials[i].checked = 0;
                                }
                            });
                        }
                    });

                });
        }
    };
}];
