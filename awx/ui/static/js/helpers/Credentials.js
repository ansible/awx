/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/
 
/**
 * @ngdoc function
 * @name helpers.function:Credentials
 * @description   Functions shared amongst Credential related controllers
 */

export default
angular.module('CredentialsHelper', ['Utilities'])

.factory('KindChange', ['Empty',
         function (Empty) {
             return function (params) {
                 var scope = params.scope,
                 reset = params.reset,
                 collapse, id;

                 $('.popover').each(function() {
                     // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                     $(this).remove();
                 });
                 $('.tooltip').each( function() {
                     // close any lingering tool tipss
                     $(this).hide();
                 });
                 // Put things in a default state
                 scope.usernameLabel = 'Username';
                 scope.aws_required = false;
                 scope.email_required = false;
                 scope.rackspace_required = false;
                 scope.sshKeyDataLabel = 'Private Key';
                 scope.username_required = false;                        // JT-- added username_required b/c mutliple 'kinds' need username to be required (GCE)
                 scope.key_required = false;                             // JT -- doing the same for key and project
                 scope.project_required = false;
                 scope.subscription_required = false;
                 scope.key_description = "Paste the contents of the SSH private key file.<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>";
                 scope.key_hint= "drag and drop an SSH private key file on the field below";
                 scope.host_required = false;
                 scope.password_required = false;
                 scope.hostLabel = '';
                 scope.passwordLabel = 'Password';

                 $('.popover').each(function() {
                     // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                     $(this).remove();
                 });
                 $('.tooltip').each( function() {
                     // close any lingering tool tipss
                     $(this).hide();
                 });
                 // Put things in a default state
                 scope.usernameLabel = 'Username';
                 scope.aws_required = false;
                 scope.email_required = false;
                 scope.rackspace_required = false;
                 scope.sshKeyDataLabel = 'Private Key';
                 scope.username_required = false;                        // JT-- added username_required b/c mutliple 'kinds' need username to be required (GCE)
                 scope.key_required = false;                             // JT -- doing the same for key and project
                 scope.project_required = false;
                 scope.subscription_required = false;
                 scope.key_description = "Paste the contents of the SSH private key file.";
                 scope.key_hint= "drag and drop an SSH private key file on the field below";
                 scope.host_required = false;
                 scope.password_required = false;
                 scope.hostLabel = '';
                 scope.projectLabel = '';
                 scope.project_required = false;
                 scope.passwordLabel = 'Password (API Key)';
                 scope.projectPopOver = "<p>The project value</p>";
                 scope.hostPopOver = "<p>The host value</p>";

                 if (!Empty(scope.kind)) {
                     // Apply kind specific settings
                     switch (scope.kind.value) {
                         case 'aws':
                             scope.aws_required = true;
                         break;
                         case 'rax':
                             scope.rackspace_required = true;
                             scope.username_required = true;
                         break;
                         case 'ssh':
                             scope.usernameLabel = 'Username'; //formally 'SSH Username'
                         break;
                         case 'scm':
                             scope.sshKeyDataLabel = 'SCM Private Key';
                             scope.passwordLabel = 'Password';
                         break;
                         case 'gce':
                             scope.usernameLabel = 'Service Account Email Address';
                             scope.sshKeyDataLabel = 'RSA Private Key';
                             scope.email_required = true;
                             scope.key_required = true;
                             scope.project_required = true;
                             scope.key_description =  'Paste the contents of the PEM file associated with the service account email.';
                             scope.key_hint= "drag and drop a private key file on the field below";
                             scope.projectLabel = "Project";
                             scope.project_required = false;
                             scope.projectPopOver = "<p>The Project ID is the " +
                             "GCE assigned identification. It is constructed as " +
                             "two words followed by a three digit number.  Such " +
                             "as: </p><p>adjective-noun-000</p>";
                         break;
                         case 'azure':
                             scope.usernameLabel = "Subscription ID";
                             scope.sshKeyDataLabel = 'Management Certificate';
                             scope.subscription_required = true;
                             scope.key_required = true;
                             scope.key_description = "Paste the contents of the PEM file that corresponds to the certificate you uploaded in the Microsoft Azure console.";
                             scope.key_hint= "drag and drop a management certificate file on the field below";
                         break;
                         case 'vmware':
                             scope.username_required = true;
                             scope.host_required = true;
                             scope.password_required = true;
                             scope.hostLabel = "vCenter Host";
                             scope.passwordLabel = 'Password';
                         break;
                         case 'openstack':
                             scope.hostLabel = "Host (Authentication URL)";
                             scope.projectLabel = "Project (Tenet Name/ID)";
                             scope.password_required = true;
                             scope.project_required = true;
                             scope.host_required = true;
                             scope.username_required = true;
                             scope.projectPopOver = "<p>This is the tenant name " +
                                 "or tenant id. This value is usually the same " +
                                 " as the username.</p>";
                             scope.hostPopOver = "<p>The host to authenticate with." +
                                 "<br />For example, https://openstack.business.com/v2.0/";
                         break;
                     }
                 }

                 // Reset all the field values related to Kind.
                 if (reset) {
                     scope.access_key = null;
                     scope.secret_key = null;
                     scope.api_key = null;
                     scope.username = null;
                     scope.password = null;
                     scope.password_confirm = null;
                     scope.ssh_key_data = null;
                     scope.ssh_key_unlock = null;
                     scope.ssh_key_unlock_confirm = null;
                     scope.become_username = null;
                     scope.become_password = null;
                 }

                 // Collapse or open help widget based on whether scm value is selected
                 collapse = $('#credential_kind').parent().find('.panel-collapse').first();
                 id = collapse.attr('id');
                 if (!Empty(scope.kind) && scope.kind.value !== '') {
                     if ($('#' + id + '-icon').hasClass('icon-minus')) {
                         scope.accordionToggle('#' + id);
                     }
                 } else {
                     if ($('#' + id + '-icon').hasClass('icon-plus')) {
                         scope.accordionToggle('#' + id);
                     }
                 }

             };
         }
])


.factory('OwnerChange', [
    function () {
    return function (params) {
        var scope = params.scope,
        owner = scope.owner;
        if (owner === 'team') {
            scope.team_required = true;
            scope.user_required = false;
            scope.user = null;
            scope.user_username = null;
        } else {
            scope.team_required = false;
            scope.user_required = true;
            scope.team = null;
            scope.team_name = null;
        }
    };
}
])

.factory('FormSave', ['$location', 'Alert', 'Rest', 'ProcessErrors', 'Empty', 'GetBasePath', 'CredentialForm', 'ReturnToCaller', 'Wait',
         function ($location, Alert, Rest, ProcessErrors, Empty, GetBasePath, CredentialForm, ReturnToCaller, Wait) {
             return function (params) {
                 var scope = params.scope,
                 mode = params.mode,
                 form = CredentialForm,
                 data = {}, fld, url;

                 for (fld in form.fields) {
                     if (fld !== 'access_key' && fld !== 'secret_key' && fld !== 'ssh_username' &&
                         fld !== 'ssh_password') {
                         if (scope[fld] === null) {
                             data[fld] = "";
                         } else {
                             data[fld] = scope[fld];
                         }
                     }
                 }

                 if (!Empty(scope.team)) {
                     data.team = scope.team;
                     data.user = "";
                 } else {
                     data.user = scope.user;
                     data.team = "";
                 }

                 data.kind = scope.kind.value;
                 if (scope.become_method === null) {
                    data.become_method = "";
                    data.become_username = "";
                    data.become_password = "";
                 } else {
                    data.become_method = (scope.become_method.value) ? scope.become_method.value : "";
                 }
                 switch (data.kind) {
                     case 'ssh':
                         data.password = scope.ssh_password;
                     break;
                     case 'aws':
                         data.username = scope.access_key;
                     data.password = scope.secret_key;
                     break;
                     case 'rax':
                         data.password = scope.api_key;
                     break;
                     case 'gce':
                         data.username = scope.email_address;
                     data.project = scope.project;
                     break;
                     case 'azure':
                         data.username = scope.subscription_id;
                 }

                 if (Empty(data.team) && Empty(data.user)) {
                     Alert('Missing User or Team', 'You must provide either a User or a Team. If this credential will only be accessed by a specific ' +
                           'user, select a User. To allow a team of users to access this credential, select a Team.', 'alert-danger');
                 } else {
                     Wait('start');
                     if (mode === 'add') {
                         url = (!Empty(data.team)) ? GetBasePath('teams') + data.team + '/credentials/' :
                             GetBasePath('users') + data.user + '/credentials/';
                         Rest.setUrl(url);
                         Rest.post(data)
                         .success(function () {
                             Wait('stop');
                             var base = $location.path().replace(/^\//, '').split('/')[0];
                                 if (base === 'credentials') {
                                 ReturnToCaller();
                             }
                             else {
                                 ReturnToCaller(1);
                             }
                         })
                         .error(function (data, status) {
                             Wait('stop');
                             ProcessErrors(scope, data, status, form, {
                                 hdr: 'Error!',
                                 msg: 'Failed to create new Credential. POST status: ' + status
                             });
                         });
                     } else {
                         url = GetBasePath('credentials') + scope.id + '/';
                         Rest.setUrl(url);
                         Rest.put(data)
                         .success(function () {
                             Wait('stop');
                             var base = $location.path().replace(/^\//, '').split('/')[0];
                                 if (base === 'credentials') {
                                 ReturnToCaller();
                             }
                             else {
                                 ReturnToCaller(1);
                             }
                         })
                         .error(function (data, status) {
                             Wait('stop');
                             ProcessErrors(scope, data, status, form, {
                                 hdr: 'Error!',
                                 msg: 'Failed to update Credential. PUT status: ' + status
                             });
                         });
                     }
                 }
             };
         }
]);
