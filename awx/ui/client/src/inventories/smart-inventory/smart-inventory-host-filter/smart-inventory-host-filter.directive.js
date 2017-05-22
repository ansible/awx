/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import smartInventoryHostFilterController from './smart-inventory-host-filter.controller';

export default ['templateUrl', '$compile',
    function(templateUrl, $compile) {
        return {
            scope: {
                hostFilter: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('inventories/smart-inventory/smart-inventory-host-filter/smart-inventory-host-filter'),
            controller: smartInventoryHostFilterController,
            link: function(scope) {
                scope.openHostFilterModal = function() {
                    $('#content-container').append($compile('<host-filter-modal host-filter="hostFilter"></host-filter-modal>')(scope));
                };
            }
        };
    }
];
