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

export default function ModelToBasePathKey() {
    return function(model) {
        // This function takes in the singular model string and returns the key needed
        // to get the base path from $rootScope/local storage.

        var basePathKey;

        switch(model) {
            case 'o_auth2_application':
                basePathKey = 'applications';
                break;
            case 'project':
                basePathKey = 'projects';
                break;
            case 'credential_type':
                basePathKey = 'credential_types';
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
            case 'notification_template':
                basePathKey = 'notification_templates';
                break;
            case 'organization':
                basePathKey = 'organizations';
                break;
            case 'management_job':
                basePathKey = 'management_jobs';
                break;
            case 'custom_inventory_script':
                basePathKey = 'inventory_scripts';
                break;
            case 'workflow_job_template':
                basePathKey = 'workflow_job_templates';
                break;
            case 'host':
                basePathKey = 'hosts';
                break;
        }

        return basePathKey;
    };
}
