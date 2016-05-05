/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'GetBasePath', function(Rest, GetBasePath){
    return {
        deleteJobTemplate: function(id){
            var url = GetBasePath('job_templates');

            url = url + id;

            Rest.setUrl(url);
            return Rest.destroy();
        }
    };
}];
