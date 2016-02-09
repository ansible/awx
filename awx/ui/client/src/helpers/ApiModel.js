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
        .factory('ModelToSingular', [
            function () {
                return function (model) {
                    // This function takes in the plural model string and spits out the singular
                    // version.

                    var singularModel;

                    switch(model) {
                        case 'projects':
                            singularModel = 'project';
                            break;
                        case 'inventories':
                            singularModel = 'inventory';
                            break;
                        case 'job_templates':
                            singularModel = 'job_template';
                            break;
                        case 'credentials':
                            singularModel = 'credential';
                            break;
                        case 'users':
                            singularModel = 'user';
                            break;
                        case 'teams':
                            singularModel = 'team';
                            break;
                        case 'organizations':
                            singularModel = 'organization';
                            break;
                        case 'management_jobs':
                            singularModel = 'management_job';
                            break;
                        case 'inventory_scripts':
                            singularModel = 'inventory_script';
                            break;
                    }

                    return singularModel;

                };
            }
        ])
        .factory('ModelToPlural', [
            function () {
                return function (model) {
                    // This function takes in the singular model string and spits out the plural
                    // version.

                    var pluralModel;

                    switch(model) {
                        case 'project':
                            pluralModel = 'projects';
                            break;
                        case 'inventory':
                            pluralModel = 'inventories';
                            break;
                        case 'job_template':
                            pluralModel = 'job_templates';
                            break;
                        case 'credential':
                            pluralModel = 'credentials';
                            break;
                        case 'user':
                            pluralModel = 'users';
                            break;
                        case 'team':
                            pluralModel = 'teams';
                            break;
                        case 'organization':
                            pluralModel = 'organizations';
                            break;
                        case 'management_job':
                            pluralModel = 'management_jobs';
                            break;
                        case 'inventory_script':
                            pluralModel = 'inventory_scripts';
                            break;
                    }

                    return pluralModel;

                };
            }
        ]);
