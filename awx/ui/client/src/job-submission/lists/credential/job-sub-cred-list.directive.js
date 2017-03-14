/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobSubCredListController from './job-sub-cred-list.controller';

export default [ 'templateUrl', 'QuerySet', 'GetBasePath', 'generateList', '$compile', 'CredentialList',
    (templateUrl, qs, GetBasePath, GenerateList, $compile, CredentialList) => {
    return {
        scope: {
          selectedCredential: '='
        },
        templateUrl: templateUrl('job-submission/lists/credential/job-sub-cred-list'),
        controller: jobSubCredListController,
        restrict: 'E',
        link: scope => {
            let toDestroy = [];

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
                .then(res => {
                    scope.credential_dataset = res.data;
                    scope.credentials = scope.credential_dataset.results;

                    let credList = _.cloneDeep(CredentialList);
                    let html = GenerateList.build({
                        list: credList,
                        input_type: 'radio',
                        mode: 'lookup'
                    });

                    scope.list = credList;

                    $('#job-submission-credential-lookup').append($compile(html)(scope));

                    toDestroy.push(scope.$watchCollection('selectedCredential', () => {
                        if(scope.selectedCredential) {
                            // Loop across the inventories and see if one of them should be "checked"
                            scope.credentials.forEach((row, i) => {
                                if (row.id === scope.selectedCredential.id) {
                                    scope.credentials[i].checked = 1;
                                }
                                else {
                                    scope.credentials[i].checked = 0;
                                }
                            });
                        }
                    }));
                });

            scope.$on('$destroy', () => toDestroy.forEach(watcher => watcher()));
        }
    };
}];
