/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

function AnsibleFacts($scope, Facts, ParseTypeChange, ParseVariableString) {

    function init() {
        $scope.facts = ParseVariableString(Facts.data);
        let rows = (_.isEmpty(Facts.data)) ? 6 : 20;
        $("#host_facts").attr("rows", rows);
        $scope.parseType = 'yaml';
        ParseTypeChange({
             scope: $scope,
             variable: 'facts',
             parse_variable: 'parseType',
             field_id: 'host_facts',
             readOnly: true
         });
    }

    init();

}

export default ['$scope', 'Facts', 'ParseTypeChange', 'ParseVariableString', AnsibleFacts
];
