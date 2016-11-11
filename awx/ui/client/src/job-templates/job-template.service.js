/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['Rest', 'GetBasePath', '$q', function(Rest, GetBasePath, $q){
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
        getLabelOptions: function(){
            var url = GetBasePath('labels');

            var deferred = $q.defer();

            Rest.setUrl(url);
            Rest.get()
            .success(function(data) {
                // Turn the labels into something consumable
                var labels = data.results.map((i) => ({label: i.name, value: i.id}));
                deferred.resolve(labels);
            }).error(function(msg, code) {
                deferred.reject(msg, code);
            });

          return deferred.promise;

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
      getWorkflowJobTemplateNodes: function(id) {
          var url = GetBasePath('workflow_job_templates');

          url = url + id + '/workflow_nodes';

          Rest.setUrl(url);
          return Rest.get();
      },
      updateWorkflowJobTemplate: function(params) {
          // params.id
          // params.data

          var url = GetBasePath('workflow_job_templates');

          url = url + params.id;

          Rest.setUrl(url);
          return Rest.put(params.data);
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
      }
    };
}];
