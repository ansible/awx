/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import jobSubCredListController from './job-sub-cred-list.controller';

export default [ 'templateUrl', '$compile', 'generateList',
    (templateUrl, $compile, GenerateList) => {
    return {
        scope: {
          selectedCredentials: '=',
          credentialKind: '=',
          credentialTypes: '='
        },
        templateUrl: templateUrl('job-submission/lists/credential/job-sub-cred-list'),
        controller: jobSubCredListController,
        restrict: 'E',
        link: scope => {
            scope.generateCredentialList = function() {
                let html = GenerateList.build({
                    list: scope.list,
                    input_type: 'radio',
                    mode: 'lookup'
                });
                $('#job-submission-credential-lookup').append($compile(html)(scope));
            };
        }
    };
}];
