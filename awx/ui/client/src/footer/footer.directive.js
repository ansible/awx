/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    ['templateUrl',
        function(templateUrl) {
            return {
                restrict: 'E',
                scope: true,
                templateUrl: templateUrl('footer/footer')
            };
        }
    ];
