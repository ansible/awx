/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 /**
 * @ngdoc function
 * @name helpers.function:ApiModel
 * @description Helper functions to convert singular/plural versions of our models to the opposite
*/

export default
    angular.module('ApiModelHelper', ['Utilities'])
        .factory('ModelToBasePathKey', [
            function () {
                return function (model) {
                    // This function takes in the singular model string and returns the key needed
                    // to get the base path from $rootScope/local storage.

                    var basePathKey;

                    switch(model) {
                        case 'project':
                            basePathKey = 'projects';
                            break;
                        case 'inventory':
                            basePathKey = 'inventory';
                            break;
                        case 'job_template':
                            basePathKey = 'job_templates';
                            break;
                        case 'credential':
                            basePathKey = 'credentials';
                            break;
                        case 'user':
                            basePathKey = 'users';
                            break;
                        case 'team':
                            basePathKey = 'teams';
                            break;
                        case 'organization':
                            basePathKey = 'organizations';
                            break;
                        case 'management_job':
                            basePathKey = 'management_jobs';
                            break;
                        case 'inventory_script':
                            basePathKey = 'inventory_scripts';
                            break;
                    }

                    return basePathKey;

                };
            }
        ]);
