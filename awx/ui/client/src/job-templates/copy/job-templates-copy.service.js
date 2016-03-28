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
	 			 		return res
	 			 	})
	 			 	.error(function(res, status){
	                    ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                    msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	                });
 			},
 			set: function(data){
	 			var defaultUrl = GetBasePath('job_templates');
	 			Rest.setUrl(defaultUrl);
	 			var name = this.buildName(data.results[0].name)
	 			data.results[0].name = name + ' @ ' + moment().format('h:mm:ss a'); // 2:49:11 pm
	 			return Rest.post(data.results[0])
	 				.success(function(res){
	 					return res
	 				})
	 				.error(function(res, status){                   
						ProcessErrors($rootScope, res, status, null, {hdr: 'Error!',
	                	msg: 'Call to '+ defaultUrl + ' failed. Return status: '+ status});
	 				});
 			},
 			buildName: function(name){
 				var result = name.split('@')[0];
 				return result
 			}
 		}
 	}
 	];