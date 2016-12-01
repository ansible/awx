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
                    .success(function(res){
                        return res;
                    })
                    .error(function(res, status){
                        ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
                        msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
                    });
            },
            getSurvey: function(endpoint){
                Rest.setUrl(endpoint);
                return Rest.get();
            },
            copySurvey: function(source, target){
                return this.getSurvey(source.related.survey_spec).success( (data) => {
                    Rest.setUrl(target.related.survey_spec);
                    return Rest.post(data);
                });
            },
            set: function(data){
                var defaultUrl = GetBasePath('job_templates');
                var self = this;
                Rest.setUrl(defaultUrl);
                var name = this.buildName(data.results[0].name);
                data.results[0].name = name + ' @ ' + moment().format('h:mm:ss a'); // 2:49:11 pm
                return Rest.post(data.results[0])
                    .success(function(job_template_res){
                        // also copy any associated survey_spec
                        if (data.results[0].summary_fields.survey){
                            return self.copySurvey(data.results[0], job_template_res).success( () => job_template_res);
                        }
                        else{
                            return job_template_res;
                        }
                    })
                    .error(function(res, status){
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
            copyWorkflow: function(id) {
                let url = GetBasePath('workflow_job_templates');

                url = url + id + '/copy';

                Rest.setUrl(url);
                return Rest.post();
            }
        };
    }
    ];
