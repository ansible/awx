/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['templateUrl', 'TemplatesStrings',
    function(templateUrl, TemplatesStrings) {
        return {
            scope: {},
            templateUrl: templateUrl('templates/workflows/workflow-key/workflow-key'),
            restrict: 'E',
            link: function(scope) {
              scope.strings = TemplatesStrings;
          }
        };
    }
];
