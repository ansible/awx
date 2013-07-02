/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
*/

angular.module('AccessHelper', ['RestServices', 'Utilities', 'ngCookies'])  
    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath','ProcessErrors', 
    function($rootScope, Alert, Rest, GetBasePath, ProcessErrors) {
    return function(params) {
       var me = $rootScope.current_user;
       var access = false;
       if (me.is_superuser) {
          access = true;
       }
       else {
          if (me.related.admin_of_organizations) {
             Rest.setUrl(me.related.admin_of_organizations);
             Rest.get()
                 .success( function(data, status, headers, config) {
                     if (data.results.length > 0) {
                        access = true;
                     }
                 })
                 .error( function(data, status, headers, config) {
                     ProcessErrors(scope, data, status, null,
                         { hdr: 'Error!', msg: 'Call to ' + me.related.admin_of_organizations + 
                         ' failed. DELETE returned status: ' + status });
                     });  
          }
       }
       if (!access) {
          Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
       }
       return access;
    }
    }])
   
    .factory('CheckLicense', ['$rootScope', '$cookieStore', 'Alert', '$location', 'Authorization',
    function($rootScope, $cookieStore, Alert, $location, Authorization) {
    return function() {   
        // Check license status and alert the user, if needed
        var status = 'success';
        var hdr, msg;
        var license = $cookieStore.get('license');
        if (license && !Authorization.licenseTested()) {
           // This is our first time evaluating the license
           license['tested'] = true; 
           $cookieStore.remove('license');
           $cookieStore.put('license', license);
           $rootScope.license_tested = true; 
           if (license['key_valid'] !== undefined && license['key_valid'] == false) {
              // The license is invalid. Stop the user from logging in.
              status = 'alert-error';
              hdr = 'License Error';
              msg = 'Something is wrong with your /etc/awx/license file on this server. ' +
                    'Please contact <a href="mailto:info@ansibleworks.com">info@ansibleworks.com</a> for assistance.';
              //action = function() { window.location = '#/logout'; };
              Alert(hdr, msg, status, null, false, true);
           }
           else if (license['demo'] !== undefined && license['demo'] == true) {
              // demo
              status = 'alert-info';
              hdr = 'AWX Demo';
              msg = 'Thank you for trying AnsibleWorks AWX. You can use this edition to manage up to 5 hosts. ' +
                    'Should you wish to acquire a license for additional servers, please visit ' + 
                    '<a href="http://ansibleworks.com/ansibleworks-awx" target="_blank"><strong>ansibleworks.com/ansibleworks-awx</strong></a>, or ' +
                    'contact <a href="mailto:info@ansibleworks.com"><strong>info@ansibleworks.com</strong></a> for assistance.';
              Alert(hdr, msg, status);
           }
           if (license['date_warning'] !== undefined && license['date_warning'] == true) {
              status = 'alert-info';
              hdr = 'License Expired';
              msg = 'Your AnsibleWorks AWX License has expired and is no longer compliant. ' + 
                    'You can continue, but you will be unable to add any additional hosts. Please ' +
                    'visit <a href="http://ansibleworks.com/ansibleworks-awx" target="_blank"><strong>ansibleworks.com/ansibleworks-awx</strong></a> ' +
                    'for license and renewal information, or contact <a href="mailto:info@ansibleworks.com"><strong>info@ansibleworks.com</strong></a> ' +
                    'for assistance.';
              Alert(hdr, msg, status);
           }
           if (license['free_instances'] !== undefined && parseInt(license['free_instances']) <= 0) {
              status = 'alert-info';
              hdr = 'License Warning'; 
              msg = 'Your AnsibleWorks AWX License has reached capacity for the number of managed ' +
                    'hosts allowed. You will not be able to add any additional hosts. To extend your license, please visit ' + 
                    '<a href="http://ansibleworks.com/ansibleworks-awx" target="_blank"><strong>ansibleworks.com/ansibleworks-awx.</strong></a>, or ' +
                    'contact <a href="mailto:info@ansibleworks.com"><strong>info@ansibleworks.com</strong></a> for more information.';
              Alert(hdr, msg, status, null, true);
           } 
        }
    }
    }]);