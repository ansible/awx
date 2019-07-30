/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'GetBasePath', '$q', 'NextPage', function(Rest, GetBasePath, $q, NextPage){
    return {
        deleteJobTemplate: function(id){
            var url = GetBasePath('job_templates');

            url = url + id;

            Rest.setUrl(url);
            return Rest.destroy();
        },
        deleteWorkflowJobTemplate: function(id) {
            var url = GetBasePath('workflow_job_templates');

            url = url + id;

            Rest.setUrl(url);
            return Rest.destroy();
        },
        createJobTemplate: function(data){
            var url = GetBasePath('job_templates');

            Rest.setUrl(url);
            return Rest.post(data);
        },
        createWorkflowJobTemplate: function(data) {
            var url = GetBasePath('workflow_job_templates');

            Rest.setUrl(url);
            return Rest.post(data);
        },
        getAllLabelOptions: function() {
            Rest.setUrl(GetBasePath('labels') + '?page_size=200');
            return Rest.get()
                .then(function(res) {
                    if (res.data.next) {
                        return NextPage({
                            url: res.data.next,
                            arrayOfValues: res.data.results
                        }).then(function(labels) {
                            return labels;
                        }).catch(function(response){
                            return $q.reject( response );
                        });
                    }
                    else {
                        return $q.resolve( res.data.results );
                    }
                }).catch(function(response){
                    return $q.reject( response );
                });
      },
      getAllJobTemplateLabels: function(id) {
          Rest.setUrl(GetBasePath('job_templates') + id + "/labels?page_size=20");
          return Rest.get()
              .then(function(res) {
                  if (res.data.next) {
                      return NextPage({
                          url: res.data.next,
                          arrayOfValues: res.data.results
                      }).then(function(labels) {
                          return labels;
                      }).catch(function(response){
                          return $q.reject( response );
                      });
                  }
                  else {
                      return $q.resolve( res.data.results );
                  }
              }).catch(function(response){
                  return $q.reject( response );
              });
        },

        getAllWorkflowJobTemplateLabels: function(id) {
            Rest.setUrl(GetBasePath('workflow_job_templates') + id + "/labels?page_size=200");
            return Rest.get()
                .then(function(res) {
                    if (res.data.next) {
                        return NextPage({
                            url: res.data.next,
                            arrayOfValues: res.data.results
                        }).then(function(labels) {
                            return labels;
                        }).catch(function(response){
                            return $q.reject( response );
                        });
                    }
                    else {
                        return $q.resolve( res.data.results );
                    }
                }).catch(function(response){
                    return $q.reject( response );
                });
        },
        getJobTemplate: function(id) {
            var url = GetBasePath('job_templates');

            url = url + id;

            Rest.setUrl(url);
            return Rest.get();
        },
        addWorkflowNode: function(params) {
            // params.url
            // params.data

            Rest.setUrl(params.url);
            return Rest.post(params.data);
        },
        editWorkflowNode: function(params) {
            // params.id
            // params.data

            var url = GetBasePath('workflow_job_template_nodes') + params.id;

            Rest.setUrl(url);
            return Rest.put(params.data);
        },
        getJobTemplateLaunchInfo: function(id) {
            var url = GetBasePath('job_templates');

            url = url + id + '/launch';

            Rest.setUrl(url);
            return Rest.get();
        },
        getWorkflowJobTemplateNodes: function(id, page) {
            var url = GetBasePath('workflow_job_templates');

            url = url + id + '/workflow_nodes?page_size=200';

            if(page) {
                url += '&page=' + page;
            }

            Rest.setUrl(url);
            return Rest.get();
        },
        updateWorkflowJobTemplate: function(params) {
            // params.id
            // params.data

            var url = GetBasePath('workflow_job_templates');

            url = url + params.id;

            Rest.setUrl(url);
            return Rest.patch(params.data);
        },
        getWorkflowJobTemplate: function(id) {
            var url = GetBasePath('workflow_job_templates');

            url = url + id;

            Rest.setUrl(url);
            return Rest.get();
        },
        deleteWorkflowJobTemplateNode: function(id) {
            var url = GetBasePath('workflow_job_template_nodes') + id;

            Rest.setUrl(url);
            return Rest.destroy();
        },
        disassociateWorkflowNode: function(params) {
            //params.parentId
            //params.nodeId
            //params.edge

            var url = GetBasePath('workflow_job_template_nodes') + params.parentId;

            if(params.edge === 'success') {
                url = url + '/success_nodes';
            }
            else if(params.edge === 'failure') {
                url = url + '/failure_nodes';
            }
            else if(params.edge === 'always') {
                url = url + '/always_nodes';
            }

            Rest.setUrl(url);
            return Rest.post({
                "id": params.nodeId,
                "disassociate": true
            });
        },
        associateWorkflowNode: function(params) {
            //params.parentId
            //params.nodeId
            //params.edge

            var url = GetBasePath('workflow_job_template_nodes') + params.parentId;

            if(params.edge === 'success') {
                url = url + '/success_nodes';
            }
            else if(params.edge === 'failure') {
                url = url + '/failure_nodes';
            }
            else if(params.edge === 'always') {
                url = url + '/always_nodes';
            }

            Rest.setUrl(url);
            return Rest.post({
                id: params.nodeId
            });
        },
        getUnifiedJobTemplate: function(id) {
            var url = GetBasePath('unified_job_templates');

            url = url + "?id=" + id;

            Rest.setUrl(url);
            return Rest.get();
        },
        getCredential: function(id) {
            var url = GetBasePath('credentials');

            url = url + id;

            Rest.setUrl(url);
            return Rest.get();
        },
        getInventory: function(id) {
            var url = GetBasePath('inventory');

            url = url + id;

            Rest.setUrl(url);
            return Rest.get();
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
        },
        getWorkflowJobTemplateOptions: function() {
            var deferred = $q.defer();

            let url = GetBasePath('workflow_job_templates');

            Rest.setUrl(url);
            Rest.options()
                .then(({data}) => {
                    deferred.resolve(data);
                }).catch(({msg, code}) => {
                    deferred.reject(msg, code);
                });

            return deferred.promise;
        },
        getJobTemplateOptions: function() {
            var deferred = $q.defer();

            let url = GetBasePath('job_templates');

            Rest.setUrl(url);
            Rest.options()
                .then(({data}) => {
                    deferred.resolve(data);
                }).catch(({msg, code}) => {
                    deferred.reject(msg, code);
                });

            return deferred.promise;
        },
        postWorkflowNodeCredential: function(params) {
            // params.id
            // params.data

            var url = GetBasePath('workflow_job_template_nodes') + params.id + '/credentials';

            Rest.setUrl(url);
            return Rest.post(params.data);
        }
    };
}];
