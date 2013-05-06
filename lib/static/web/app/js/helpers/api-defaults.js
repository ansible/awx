/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * APIDefaults
 *
 * 
 */

angular.module('APIDefaults', ['RestServices', 'Utilities'])  
    .factory('GetAPIDefaults', ['Alert', 'Rest', '$rootScope', function(Alert, Rest, $rootScope) {
    return function(key) {
    
    //Reload a related collection on pagination or search change
    
    var answer; 
    var result = {};
    var cnt=0;

    function lookup(key) {
        var result = {};
        for (id in $rootScope.apiDefaults) {
            if (id == key || id.iterator == key) {
               result[id] = defaults[id];
               break;
            }
        }
        return result;
    }

    function wait() {
        var answer;
        if ( result == {} && cnt < 5) {
           cnt++;
           setTimeout(1000, wait());
        }
        else {
           if (result.status == 'success') {
              return lookup(key);
           }
        }
    }

    if ($rootScope.apiDefaults == null || $rootScope.apiDefaults == undefined) {
       var result = {};
       var url = '/api/v1';
       Rest.setUrl(url);
       Rest.get()
           .success( function(data, status, headers, config) {
               defaults = data;
               for (var id in defaults) {
                   switch (id) {
                       case 'organizations':
                            dafaults[id].iterator = 'organization';
                            break;
                       case 'jobs':
                            defaults[id].iterator = 'job';
                            break;
                       case 'users':
                            defaults[id].iterator = 'user';
                            break;
                       case 'teams':
                            defaults[id].iterator = 'team';
                            break;
                       case 'hosts':
                            defaults[id].iterator = 'host';
                            break;
                       case 'groups':
                            defaults[id].iterator = 'group';
                            break; 
                       case 'projects':
                            defaults[id].iterator = 'project';
                            break; 
                   }    
               }
               $rootScope.apiDefaults = defaults;
               result = {status: 'success'};
               })
           .error( function(data, status, headers, config) {
               result = {status: 'error', msg: 'Call to ' + url + ' failed. GET returned status: ' + status};
               });
        return wait();
     }
     else {
        return lookup(key);
     }
     
     }

}]);
