/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import dynamicInventoryHostFilterController from './dynamic-inventory-host-filter.controller';

export default ['templateUrl', '$compile',
    function(templateUrl, $compile) {
        return {
            scope: {
                hostFilter: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('inventories/hosts/smart-inventory/dynamic-inventory-host-filter/dynamic-inventory-host-filter'),
            controller: dynamicInventoryHostFilterController,
            link: function(scope) {
                scope.openHostFilterModal = function() {
                    $('#content-container').append($compile('<host-filter-modal host-filter="hostFilter"></host-filter-modal>')(scope));
                };
            }
        };
    }
];
