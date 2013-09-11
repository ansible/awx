/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  UserHelper
 *  Routines shared amongst the user controllers 
 */
 
angular.module('UserHelper', [ 'UserFormDefinition' ])  
    .factory('ResetForm', ['UserForm', function(UserForm) {
    return function() {
        // Restore form to default conditions.  Run before applying LDAP configuration. 
        // LDAP may manage some or all of these fields in which case the user cannot
        // make changes to their values in AWX.

       UserForm.fields['first_name'].readonly = false; 
       UserForm.fields['first_name'].editRequired = true;
       UserForm.fields['last_name'].readonly = false; 
       UserForm.fields['last_name'].editRequired = true; 
       UserForm.fields['email'].readonly = false; 
       UserForm.fields['email'].editRequired = true; 
       UserForm.fields['organization'].awRequiredWhen = { variable: "orgrequired", init: true};
       UserForm.fields['organization'].readonly = false;
       UserForm.fields['username'].awRequiredWhen = { variable: "not_ldap_user", init: true };
       UserForm.fields['username'].readonly = false;
       UserForm.fields['password'].awRequiredWhen = { variable: "not_ldap_user", init: true },
       UserForm.fields['password'].readonly = false;

    }
    }]);