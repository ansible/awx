/*****************************************
 * License.js
 *
 * View license info: /api/vi/config/
 *
 *****************************************/

'use strict';

angular.module('License', ['RestServices', 'Utilities', 'FormGenerator', 'PromptDialog'])
   .factory('ViewLicense', ['$location', 'GenerateForm', 'Rest', 'Alert', 'GetBasePath', 'ProcessErrors',
       'FormatDate', 'Prompt',
   function($location, GenerateForm, Rest, Alert, GetBasePath, ProcessErrors, FormatDate, Prompt) {
   return function() {
   
   var defaultUrl=GetBasePath('config');
   var generator = GenerateForm;
   
   var form = {
       name: 'license',
       well: false,
       forceListeners: true,
       'class': 'horizontal-narrow',                                            
       fields: {
           license_status: {
               label: 'Status',
               type: 'custom',
               control: '<div ng-class=\"status_color\" class=\"license-status\"><i class="icon-circle"></i> \{\{ license_status \}\}</div>',
               readonly: true,
               section: 'License'
               },
           license_key: {
               label: 'Key',
               type: 'textarea',
               section: 'License',
               'class': 'modal-input-xlarge',
               readonly: true
               },
           license_date: {
               label: 'Expires On',
               type: 'text',
               readonly: true,
               section: 'License'
               },
           time_remaining: {
               label: 'Time Left',
               type: 'text',
               readonly: true,
               section: 'License'
               },
           available_instances: {
               label: 'Available',
               type: 'text',
               readonly: true,
               section: 'Managed Hosts'
               },
           current_instances: {
               label: 'Used',
               type: 'text',
               readonly: true,
               section: 'Managed Hosts'
               },
           free_instances: {
               label: 'Remaining',
               type: 'text',
               readonly: true,
               section: 'Managed Hosts',
               controlNGClass: 'free_instances_class',
               labelNGClass: 'free_instances_class'
               },
           company_name: {
               label: 'Company',
               type: 'text',
               readonly: true,
               section: 'Contact Info'
               },
           contact_name: {
               label: 'Contact',
               type: 'text',
               readonly: true,
               section: 'Contact Info'
               },
            contact_email: {
               label: 'Contact Email',
               type: 'text',
               readonly: true,
               section: 'Contact Info'
               }
            }
        };

   var base = $location.path().replace(/^\//,'').split('/')[0]; 
   

   function empty(x) {
       var result = false;
       if (x != 0 && (x === null || x === undefined || x == '') ) {
          result = true;
       }
       return result;
   }
                
   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get()
       .success( function(data, status, headers, config) {
           for (var fld in form.fields) {
              if (fld != 'time_remaining' && fld != 'license_status') {
                 if (empty(data['license_info'][fld])) {
                    delete form.fields[fld];
                 }
              }
           }

           if (empty(data['license_info']['license_date'])) {
              delete form.fields['license_date'];
              delete form.fields['time_remaining'];
           }

           var scope = generator.inject(form, { mode: 'edit', modal: true, related: false});
           generator.reset();
           
           scope.formModalAction = function() {
               $('#form-modal').modal("hide");
               }
           
           scope.formModalActionLabel = 'OK';
           scope.formModalCancelShow = false;
           scope.formModalInfo = 'Purchase/Extend License';
           $('#form-modal .btn-success').removeClass('btn-success').addClass('btn-none');
           $('#form-modal').addClass('skinny-modal');
           scope.formModalHeader = 'AWX License';

           // Respond to license button
           scope.formModalInfoAction = function() {
               Prompt({
                   hdr: 'AWX Licensing',
                   body: "<p>AWX licenses can be purchased or extended by visiting <a id=\"license-link\" " +
                       "href=\"http://store.ansibleworks.com\" target=\"_blank\">" +
                       "the AnsibleWorks online store</a>. Would you like to purchase or extend your license now?</p>",
                   'class': 'btn-primary', 
                   action: function() { 
                       var href = $('#license-link').attr('href'); 
                       window.open(href, 'storeWindow'); 
                       }
                   });
               }

           for (var fld in form.fields) {
               if (data['license_info'][fld] !== undefined) {
                  scope[fld] = data['license_info'][fld];
               }
           }

           if (scope['license_date']) {
              var dt = new Date(parseInt(scope['license_date']));
              if (dt.getFullYear() == '1970') {
                 // date was passed in seconds rather than milliseconds
                 dt = new Date(parseInt(scope['license_date']) * 1000);
                 scope['time_remaining'] = scope['time_remaining'] + '000';
              } 
              scope['license_date'] = FormatDate(dt);

              var days = parseInt(scope['time_remaining'] / 86400000);
              var remainder = scope['time_remaining'] - (days * 86400000);
              var hours = parseInt(remainder / 3600000);
              remainder = remainder - (hours * 3600000);
              var minutes = parseInt(remainder / 60000);
              remainder = remainder - (minutes * 60000);
              var seconds = parseInt(remainder / 1000);
              scope['time_remaining'] = days + ' days ' + ('0' + hours).slice(-2) + ':' + ('0' + minutes).slice(-2) + ':' + ('0' + seconds).slice(-2); 
           }

           if (parseInt(scope['free_instances']) <= 0) {
              scope['free_instances_class'] = 'field-failure';
           }
           else {
              scope['free_instances_class'] = 'field-success';
           }

           var license = data['license_info'];
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
              scope['license_status'] = 'No available managed hosts';
              scope['status_color'] = 'license-invalid';
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
