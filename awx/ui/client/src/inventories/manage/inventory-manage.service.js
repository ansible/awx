/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default
 	['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', function($rootScope, Rest, GetBasePath, ProcessErrors){
 		return {
		getRootGroups: function(id){
			var url = GetBasePath('inventory') + id + '/root_groups/';
			Rest.setUrl(url);
			return Rest.get()
				.success(function(data){
					return data.results;
				})
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
 			}
 		};
 	}];