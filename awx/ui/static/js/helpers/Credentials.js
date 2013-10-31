/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Credentials.js
 *
 *  Functions shared amongst Credential related controllers
 *
 */

angular.module('CredentialsHelper', ['Utilities'])  
    
    .factory('KindChange', [ function() {
    return function(params) {
      
        var scope = params.scope; 
        var form = params.form;
        var reset = params.reset;

        // Set field lables
        if (scope.kind.value !== 'ssh') {
           scope['usernameLabel'] = 'Username';
           scope['passwordLabel'] = 'Password';
           scope['passwordConfirmLabel'] = 'Confirm Password';
           scope['sshKeyDataLabel'] = 'SCM Private Key';
        }
        else {
           scope['usernameLabel'] = 'SSH Username';
           scope['passwordLabel'] = 'SSH Password';
           scope['passwordConfirmLabel'] = 'Confirm SSH Password';
           scope['sshKeyDataLabel'] = 'SSH Private Key';
        }
       
        scope['aws_required'] = (scope.kind.value == 'aws') ? true : false;
        
        if (scope.kind.value == 'rax') {
            scope['rackspace_required'] = true;
            form.fields['password'].clear = true; 
            form.fields['password'].ask = true; 
        }
        else {
            scope['rackspace_required'] = false;
            form.fields['password'].clear = false; 
            form.fields['password'].ask = false; 
        }

        // Reset all the fields related to Kind.
        if (reset) {
           scope['access_key'] = null;
           scope['secret_key'] = null;
           scope['username'] = null;
           scope['password'] = null;
           scope['password_confirm'] = null;
           scope['ssh_key_data'] = null;
           scope['ssh_key_unlock'] = null;
           scope['ssh_key_unlock_confirm'] = null;
           scope['sudo_username'] = null;
           scope['sudo_password'] = null;
           scope['sudo_password_confirm'] = null;
        }

        }
        }]);
        