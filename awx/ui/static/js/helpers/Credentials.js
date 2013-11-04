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

        // Put things in a default state
        scope['usernameLabel'] = 'Username';
        scope['aws_required'] = false;
        scope['rackspace_required'] = false;
        scope['sshKeyDataLabel'] = 'SSH Private Key';
        
        // Apply kind specific settings
        switch(scope['kind'].value) {
            case 'aws':
                scope['aws_required'] = true;
                break; 
            case 'rax': 
                scope['rackspace_required'] = true;
                break;
            case 'ssh':
                scope['usernameLabel'] = 'SSH Username';
                break; 
            case 'scm':
                scope['sshKeyDataLabel'] = 'SCM Private Key';
                break;
        } 

        // Reset all the field values related to Kind.
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
        }])

    .factory('OwnerChange', [ function() {
    return function(params) {
        var scope = params.scope;
        var owner = scope['owner'];
        if (owner == 'team') {
           scope['team_required'] = true;
           scope['user_required'] = false;
           scope['user'] = null;
           scope['user_username'] = null;
        }
        else {
           scope['team_required'] = false;
           scope['user_required'] = true;
           scope['team'] = null;
           scope['team_name'] = null;
        }

        }
        }]);        