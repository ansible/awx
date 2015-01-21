angular.module('DataServices', [])
  .service('jobStatusGraphData',
           ["RestServices",
            "GetBasePath",
            "ProcessErrors",
            "$rootScope",
            "$q",
            JobStatusGraphData]);

function JobStatusGraphData(Rest, getBasePath, processErrors, $rootScope, $q) {
 var callbacks = {};
 var currentCallbackId = 0;

 function getData() {
   return Rest.get();
 }

 return {
   setupWatcher: function() {
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

     this.setupWatcher();

     return getData();

   }
 };
}
