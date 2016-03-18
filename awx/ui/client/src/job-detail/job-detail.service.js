export default
	['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', function($rootScope, Rest, GetBasePath, ProcessErrors){
		return {

			/* 
        	For ES6 
        	it might be useful to set some default params here, e.g.
        	getJobHostSummaries: function(id, page_size=200, order='host_name'){}
        	without ES6, we'd have to supply defaults like this:
        	this.page_size = params.page_size ? params.page_size : 200;
			*/

			// GET events related to a job run
			// e.g. 
			// ?event=playbook_on_stats
			// ?parent=206&event__startswith=runner&page_size=200&order=host_name,counter
			getRelatedJobEvents: function(id, params){
				var url = GetBasePath('jobs');
				url = url + id + '/job_events/?';
				Object.keys(params).forEach(function(key, index) {
					// the API is tolerant of extra ampersands
					// ?&event=playbook_on_start == ?event=playbook_on_stats
					url = url + '&' + key + '=' + params[key];
				});
				Rest.setUrl(url);
				return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});			
            },
            // GET job host summaries related to a job run
            // e.g. ?page_size=200&order=host_name
            getJobHostSummaries: function(id, params){
            	var url = GetBasePath('jobs');
            	url = url + id + '/job_host_summaries/?'
				Object.keys(params).forEach(function(key, index) {
					// the API is tolerant of extra ampersands
					url = url + '&' + key + '=' + params[key];
				});
            	Rest.setUrl(url);
            	return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});	            		
            },
            // GET job plays related to a job run
            // e.g. ?page_size=200
            getJobPlays: function(id, params){
            	var url = GetBasePath('jobs');
            	url = url + id + '/job_plays/?';
				Object.keys(params).forEach(function(key, index) {
					// the API is tolerant of extra ampersands
					url = url + '&' + key + '=' + params[key];
				});
            	Rest.setUrl(url);
            	return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});	
            },
            getJobTasks: function(id, params){
            	var url = GetBasePath('jobs');
            	url = url + id + '/job_tasks/?';
				Object.keys(params).forEach(function(key, index) {
					// the API is tolerant of extra ampersands
					url = url + '&' + key + '=' + params[key];
				});
            	Rest.setUrl(url);
            	return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});	            	
            },
            getJob: function(id){
            	var url = GetBasePath('jobs');
            	url = url + id;
            	Rest.setUrl(url);
            	return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});	
            },
            // GET next set of paginated results
            // expects 'next' param returned by the API e.g.
            // "/api/v1/jobs/51/job_plays/?order_by=id&page=2&page_size=1"
            getNextPage: function(url){
            	return Rest.get()
					.success(function(data){
						return data
					})
                    .error(function(data, status) {
                        ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + '. GET returned: ' + status });
                   	});	
            }
		}
	}
	];