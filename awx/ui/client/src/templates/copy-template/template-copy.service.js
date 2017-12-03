/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
    ['$rootScope', 'Rest', 'ProcessErrors', 'GetBasePath', 'moment',
    function($rootScope, Rest, ProcessErrors, GetBasePath, moment){
        return {
            get: function(id){
                var defaultUrl = GetBasePath('job_templates') + '?id=' + id;
                Rest.setUrl(defaultUrl);
                return Rest.get()
                    .then(response => response)
                    .catch((error) => {
                        ProcessErrors($rootScope, error.response, error.status, null, {hdr: 'Error!',
                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
                    });
            },
            getSurvey: function(endpoint){
                Rest.setUrl(endpoint);
                return Rest.get();
            },
            copySurvey: function(source, target){
                return this.getSurvey(source.related.survey_spec).then( (response) => {
                    Rest.setUrl(target.related.survey_spec);
                    return Rest.post(response.data);
                });
            },
            set: function(results){
                var defaultUrl = GetBasePath('job_templates');
                var self = this;
                Rest.setUrl(defaultUrl);
                var name = this.buildName(results[0].name);
                results[0].name = name + ' @ ' + moment().format('h:mm:ss a'); // 2:49:11 pm
                return Rest.post(results[0])
                    .then((response) => {
                        // also copy any associated survey_spec
                        if (results[0].summary_fields.survey){
                            return self.copySurvey(results[0], response.data).then( () => response.data);
                        }
                        else {
                            return response.data;
                        }
                    })
                    .catch(({res, status}) => {
                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
                    });
            },
            buildName: function(name){
                var result = name.split('@')[0];
                return result;
            },
            getWorkflowCopy: function(id) {
                let url = GetBasePath('workflow_job_templates');

                url = url + id + '/copy';

                Rest.setUrl(url);
                return Rest.get();
            },
            getWorkflowCopyName: function(baseName) {
                return `${baseName}@${moment().format('h:mm:ss a')}`;
            },
            copyWorkflow: function(id, name) {
                let url = GetBasePath('workflow_job_templates');

                url = url + id + '/copy';

                Rest.setUrl(url);
                return Rest.post({ name });
            }
        };
    }
    ];
