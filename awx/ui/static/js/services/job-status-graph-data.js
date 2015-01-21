angular.module('DataServices', [])
  .service('jobStatusGraphData',
           ["Rest",
            "GetBasePath",
            "ProcessErrors",
            "$rootScope",
            "$q",
            JobStatusGraphData]);

function JobStatusGraphData(Rest, getBasePath, processErrors, $rootScope, $q) {
 var callbacks = {};
 var currentCallbackId = 0;

 function getData(period, jobType) {
   var url = getBasePath('dashboard')+'graphs/jobs/?period='+period+'&job_type='+jobType;
   Rest.setUrl(url);
   return Rest.get();
 }

 return {
   destroyWatcher: angular.noop,
   setupWatcher: function() {
     this.destroyWatcher =
       $rootScope.$on('JobStatusChange', function() {
         getData().then(function(result) {
           $rootScope.
             $broadcast('DataReceived:JobStatusGraph',
                        result);
            return result;
         }).catch(function(response) {
           var errorMessage = 'Failed to get: ' + url + ' GET returned: ' + status;

           ProcessErrors(null,
                         response.data,
                         response.status,
                         null, {
                           hdr: 'Error!',
                           msg: errorMessage
                         });
           return response;
         });
     });
   },
   get: function(period, jobType) {

     this.destroyWatcher();
     this.setupWatcher();

     return getData(period, jobType);

   }
 };
}
