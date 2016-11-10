/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	[ 'Wait', '$state', '$scope', 'jobTemplateCopyService',
   'ProcessErrors', '$rootScope',
 	function(Wait, $state, $scope, jobTemplateCopyService,
   ProcessErrors, $rootScope){
  	// GETs the job_template to copy
 		// POSTs a new job_template
 		// routes to JobTemplates.edit when finished
 		var init = function(){
 			Wait('start');
 			jobTemplateCopyService.get($state.params.id)
 				.success(function(res){
 					jobTemplateCopyService.set(res)
            .success(function(res){
              Wait('stop');
              if(res.type && res.type === 'job_template') {
                  $state.go('templates.editJobTemplate', {id: res.id}, {reload: true});
              }
              // Workflow edit to be implemented post 3.1 but we'll need to handle the
              // state transition for that here
            });
 				})
  			.error(function(res, status){
          ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
             msg: 'Call failed. Return status: '+ status});
        });
 		};
 		init();
 	}
 	];
