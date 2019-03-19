/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function AnsibleFacts($scope, Facts) {

    function init() {
        $scope.facts = Facts;
        let rows = (_.isEmpty(Facts)) ? 6 : 20;
        $("#host_facts").attr("rows", rows);
        $scope.parseType = 'yaml';
    }

    init();

}

export default ['$scope', 'Facts', AnsibleFacts];
