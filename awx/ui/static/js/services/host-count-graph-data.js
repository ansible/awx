angular.module('DataServices')
  .service('hostCountGraphData',
           ["Rest",
            "GetBasePath",
            "ProcessErrors",
            "$q",
            HostCountGraphData]);

function HostCountGraphData(Rest, getBasePath, processErrors, $q) {

 function pluck(property, promise) {
   return promise.then(function(value) {
     return value[property];
   });
 }

   function getLicenseData() {
      url = getBasePath('config');
      Rest.setUrl(url);
      return Rest.get()
        .then(function (data){
          license = data.data.license_info.instance_count;
          return license;
        })
   }

   function getHostData() {
      url = getBasePath('dashboard')+'graphs/inventory/';
      Rest.setUrl(url);
      return pluck('data', Rest.get());
   }

  return {
    get: function() {
      return $q.all({
        license: getLicenseData(),
        hosts: getHostData()
      }).catch(function (data, status) {
          processErrors(null, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to get: ' + url + ' GET returned: ' + status });
        });
    }
  };
}
