/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 */

angular.module('AccessHelper', ['RestServices', 'Utilities', 'ngCookies'])  
    .factory('CheckAccess', ['$rootScope', 'Alert', 'Rest', 'GetBasePath','ProcessErrors', 
    function($rootScope, Alert, Rest, GetBasePath, ProcessErrors) {
    return function(params) {
       // set PermissionAddAllowed to true or false based on user access. admins and org admins are granted
       // accesss.
       var me = $rootScope.current_user;
       var scope = params.scope;

       if (me.is_superuser) {
          scope.PermissionAddAllowed = true;
       }
       else {
          if (me.related.admin_of_organizations) {
             Rest.setUrl(me.related.admin_of_organizations);
             Rest.get()
                 .success( function(data, status, headers, config) {
                     if (data.results.length > 0) {
                        scope.PermissionAddAllowed = true;
                     }
                     else {
                        scope.PermissionAddAllowed = false;
                     }
                 })
                 .error( function(data, status, headers, config) {
                     ProcessErrors(scope, data, status, null,
                         { hdr: 'Error!', msg: 'Call to ' + me.related.admin_of_organizations + 
                         ' failed. DELETE returned status: ' + status });
                     });  
          }
       }
       //if (!access) {
       //   Alert('Access Denied', 'You do not have access to this function. Please contact your system administrator.');
       //}
       //return access;
    }
    }])
   
    .factory('CheckLicense', ['$rootScope', '$cookieStore', 'Alert', '$location', 'Authorization',
    function($rootScope, $cookieStore, Alert, $location, Authorization) {
    return function() {   
        // Check license status and alert the user, if needed
        var status = 'success';
        var hdr, msg;
        var license = $cookieStore.get('license');
        
        var purchase_msg = '<p>To purchase a license or extend an existing license ' +
            '<a href="http://store.ansibleworks.com" target="_blank"><strong>visit the Ansible online store</strong></a>, ' +
            'or visit <a href="https://support.ansible.com/anonymous_requests/new">support.ansible.com</a> for assistance.</p>';

        if (license && !Authorization.licenseTested()) {
           // This is our first time evaluating the license
           license['tested'] = true; 
           $cookieStore.remove('license');
           $cookieStore.put('license', license);
           $rootScope.license_tested = true; 
           if (license['valid_key'] !== undefined && license['valid_key'] == false) {
              // The license is invalid. Stop the user from logging in.
              status = 'alert-danger';
              hdr = 'License Error';
              msg = '<p>There is a problem with the /etc/awx/license file on your Tower server. Check to make sure Tower can access ' +
                  'the file.<p>' + purchase_msg;
              Alert(hdr, msg, status, null, false, true);
           }
           else if (license['demo'] !== undefined && license['demo'] == true) {
              // demo
              status = 'alert-info';
              hdr = 'Tower Demo';
              msg = '<p>Thank you for trying Ansible Tower. You can use this edition to manage up to 10 hosts free.<p>' + 
                  purchase_msg;
              Alert(hdr, msg, status);
           }
           if (license['date_expired'] !== undefined && license['date_expired'] == true) {
              // expired
              status = 'alert-info';
              hdr = 'License Expired';
              msg = '<p>Your Ansible Tower License has expired and is no longer compliant. You can continue, but you will be ' +
                  'unable to add any additional hosts.<p>' + purchase_msg; 
              Alert(hdr, msg, status);
           }
           else if (license['date_warning'] !== undefined && license['date_warning'] == true) {
              status = 'alert-info';
              hdr = 'License Warning';
              msg = '<p>Your Ansible Tower license is about to expire!</p>' + purchase_msg;
              Alert(hdr, msg, status);
           }
           if (license['free_instances'] !== undefined && parseInt(license['free_instances']) <= 0) {
              status = 'alert-info';
              hdr = 'License Warning'; 
              msg = '<p>Your Ansible Tower license has reached capacity for the number of managed ' +
                    'hosts allowed. You will not be able to add any additional hosts.</p>' + purchase_msg;
              Alert(hdr, msg, status, null, true);
           } 
        }
    }
    }]);
