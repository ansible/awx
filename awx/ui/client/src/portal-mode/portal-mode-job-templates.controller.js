/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export function PortalModeJobTemplatesController($scope, PortalJobTemplateList, Dataset) {
    var list = PortalJobTemplateList;
    // search init
    $scope.list = list;
    $scope[`${list.iterator}_dataset`] = Dataset.data;
    $scope[list.name] = $scope[`${list.iterator}_dataset`].results;
}

PortalModeJobTemplatesController.$inject = ['$scope','PortalJobTemplateList', 'job_templatesDataset'];
