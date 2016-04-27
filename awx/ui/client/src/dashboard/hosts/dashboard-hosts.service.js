export default
	['$rootScope', 'Rest', 'GetBasePath', 'ProcessErrors', function($rootScope, Rest, GetBasePath, ProcessErrors){
		return {

		setHostStatus: function(host, enabled){
			var url = GetBasePath('hosts') + host.id;
			Rest.setUrl(url);
			return Rest.put({enabled: enabled, name: host.name})
				.success(function(data){
					return data;
				})
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
		},
		putHost: function(host){
			var url = GetBasePath('hosts') + host.id;
			Rest.setUrl(url);
			return Rest.put(host)
				.success(function(data){
					return data;
				})
                .error(function(data, status) {
                    ProcessErrors($rootScope, data, status, null, { hdr: 'Error!',
                        msg: 'Call to ' + url + '. GET returned: ' + status });
                });
		}
		};
	}];