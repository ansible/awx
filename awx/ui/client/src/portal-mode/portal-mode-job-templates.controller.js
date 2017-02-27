/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobTemplatesController($scope, PortalJobTemplateList, InitiatePlaybookRun, Dataset) {

    var list = PortalJobTemplateList;

    init();

    function init() {
        // search init
        $scope.list = list;
        $scope[`${list.iterator}_dataset`] = Dataset.data;
        $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
    }

    $scope.submitJob = function(id) {
        InitiatePlaybookRun({ scope: $scope, id: id, job_type: 'job_template' });
    };

}

PortalModeJobTemplatesController.$inject = ['$scope','PortalJobTemplateList', 'InitiatePlaybookRun', 'job_templatesDataset'];
