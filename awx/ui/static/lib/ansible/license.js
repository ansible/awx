/*****************************************
 * License.js
 *
 * View license info: /api/vi/config/
 *
 *****************************************/

'use strict';

angular.module('License', ['LicenseFormDefinition', 'RestServices', 'Utilities', 'FormGenerator'])
   .factory('ViewLicense', ['$location', 'LicenseForm', 'GenerateForm', 'Rest', 'Alert', 'GetBasePath', 'ProcessErrors', 
   function($location, LicenseForm, GenerateForm, Rest, Alert, GetBasePath, ProcessErrors) {
   return function() {
   
   var defaultUrl=GetBasePath('config');
   var generator = GenerateForm;
   var form = LicenseForm;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   
   // load the form
   var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
   generator.reset();
   scope.formModalAction = function() {
       $('#form-modal').modal("hide");
       }
   scope.formModalActionLabel = 'OK';
   scope.formModalCancelShow = false;
   scope.formModalInfo = false;
   $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
   $('#form-modal').addClass('skinny-modal');
   scope.formModalHeader = 'AWX License';
                
   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get()
       .success( function(data, status, headers, config) {
           for (var fld in form.fields) {
              if (data['license_info'][fld]) {
                 scope[fld] = data['license_info'][fld];
              }
           }
           var license = data['license_info'][fld];
           if (license['valid_key'] !== undefined && license['valid_key'] == false) {
              scope['license_status'] = 'Invalid';
              scope['status_color'] = 'license-invalid';
           }
           else if (license['demo'] !== undefined && license['demo'] == true) {
              scope['license_status'] = 'Demo';
              scope['status_color'] = 'license-demo';
           }
           else if (license['date_warning'] !== undefined && license['date_warning'] == true) {
              scope['license_status'] = 'Expired';
              scope['status_color'] = 'license-expired';
           }
           else if (license['free_instances'] !== undefined && parseInt(license['free_instances']) <= 0) {
              scope['license_status'] = 'No available servers';
              scope['status_color'] = 'license-warning';
           }
           else {
              scope['license_status'] = 'Valid';
              scope['status_color'] = 'license-valid';
           }
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
               { hdr: 'Error!', msg: 'Failed to retrieve license. GET status: ' + status });
           });
   }
   }]);
