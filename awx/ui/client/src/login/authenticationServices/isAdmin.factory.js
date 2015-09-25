/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name 
 * @description
 *
 *
 */

 export default
    ['$rootScope', function($rootScope) {
        return function() { return ($rootScope.current_user && $rootScope.current_user.is_superuser); };
    }];
