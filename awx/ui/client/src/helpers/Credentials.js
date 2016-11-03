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

.factory('KindChange', ['Empty', 'i18n',
         function (Empty, i18n) {
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
                 scope.usernameLabel = i18n._('Username');
                 scope.aws_required = false;
                 scope.email_required = false;
                 scope.rackspace_required = false;
                 scope.sshKeyDataLabel = i18n._('Private Key');
                 scope.username_required = false;                        // JT-- added username_required b/c mutliple 'kinds' need username to be required (GCE)
                 scope.key_required = false;                             // JT -- doing the same for key and project
                 scope.project_required = false;
                 scope.subscription_required = false;
                 scope.key_description = i18n._("Paste the contents of the SSH private key file.<div class=\"popover-footer\"><span class=\"key\">esc</span> or click to close</div>");
                 scope.host_required = false;
                 scope.password_required = false;
                 scope.hostLabel = '';
                 scope.passwordLabel = i18n._('Password');

                 $('.popover').each(function() {
                     // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                     $(this).remove();
                 });
                 $('.tooltip').each( function() {
                     // close any lingering tool tipss
                     $(this).hide();
                 });
                 // Put things in a default state
                 scope.usernameLabel = i18n._('Username');
                 scope.aws_required = false;
                 scope.email_required = false;
                 scope.rackspace_required = false;
                 scope.sshKeyDataLabel = i18n._('Private Key');
                 scope.username_required = false;                        // JT-- added username_required b/c mutliple 'kinds' need username to be required (GCE)
                 scope.key_required = false;                             // JT -- doing the same for key and project
                 scope.project_required = false;
                 scope.domain_required = false;
                 scope.subscription_required = false;
                 scope.key_description = i18n._("Paste the contents of the SSH private key file.");
                 scope.host_required = false;
                 scope.password_required = false;
                 scope.hostLabel = '';
                 scope.projectLabel = '';
                 scope.domainLabel = '';
                 scope.project_required = false;
                 scope.passwordLabel = i18n._('Password (API Key)');
                 scope.projectPopOver = i18n._("<p>The project value</p>");
                 scope.hostPopOver = i18n._("<p>The host value</p>");
                 scope.ssh_key_data_api_error = '';
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
                             scope.usernameLabel = i18n._('Username'); //formally 'SSH Username'
                             scope.becomeUsernameLabel = i18n._('Privilege Escalation Username');
                             scope.becomePasswordLabel = i18n._('Privilege Escalation Password');
                         break;
                         case 'scm':
                             scope.sshKeyDataLabel = i18n._('SCM Private Key');
                             scope.passwordLabel = i18n._('Password');
                         break;
                         case 'gce':
                             scope.usernameLabel = i18n._('Service Account Email Address');
                             scope.sshKeyDataLabel = i18n._('RSA Private Key');
                             scope.email_required = true;
                             scope.key_required = true;
                             scope.project_required = true;
                             scope.key_description =  i18n._('Paste the contents of the PEM file associated with the service account email.');
                             scope.projectLabel = i18n._("Project");
                             scope.project_required = false;
                             scope.projectPopOver = i18n._("<p>The Project ID is the " +
                             "GCE assigned identification. It is constructed as " +
                             "two words followed by a three digit number.  Such " +
                             "as: </p><p>adjective-noun-000</p>");
                         break;
                         case 'azure':
                             scope.sshKeyDataLabel = i18n._('Management Certificate');
                             scope.subscription_required = true;
                             scope.key_required = true;
                             scope.key_description = i18n._("Paste the contents of the PEM file that corresponds to the certificate you uploaded in the Microsoft Azure console.");
                         break;
                         case 'azure_rm':
                             scope.usernameLabel = i18n._("Username");
                             scope.subscription_required = true;
                             scope.passwordLabel = i18n._('Password');
                             scope.azure_rm_required = true;
                         break;
                         case 'vmware':
                             scope.username_required = true;
                             scope.host_required = true;
                             scope.password_required = true;
                             scope.hostLabel = "vCenter Host";
                             scope.passwordLabel = i18n._('Password');
                             scope.hostPopOver = i18n._("Enter the hostname or IP address which corresponds to your VMware vCenter.");
                         break;
                         case 'openstack':
                             scope.hostLabel = i18n._("Host (Authentication URL)");
                             scope.projectLabel = i18n._("Project (Tenant Name)");
                             scope.domainLabel = i18n._("Domain Name");
                             scope.password_required = true;
                             scope.project_required = true;
                             scope.host_required = true;
                             scope.username_required = true;
                             scope.projectPopOver = i18n._("<p>This is the tenant name. " +
                                 " This value is usually the same " +
                                 " as the username.</p>");
                             scope.hostPopOver = i18n._("<p>The host to authenticate with." +
                                 "<br />For example, https://openstack.business.com/v2.0/");
                         break;
                         case 'satellite6':
                            scope.username_required = true;
                            scope.password_required = true;
                            scope.passwordLabel = i18n._('Password');
                            scope.host_required = true;
                            scope.hostLabel = i18n._("Satellite 6 Host");
                            scope.hostPopOver = i18n._("Enter the hostname or IP address name which <br />" +
                                "corresponds to your Red Hat Satellite 6 server.");
                         break;
                         case 'cloudforms':
                            scope.username_required = true;
                            scope.password_required = true;
                            scope.passwordLabel = i18n._('Password');
                            scope.host_required = true;
                            scope.hostLabel = i18n._("CloudForms Host");
                            scope.hostPopOver = i18n._("Enter the hostname or IP address for the virtual <br />" +
                                " machine which is hosting the CloudForm appliance.");
                         break;
                         case 'net':
                            scope.username_required = true;
                            scope.password_required = false;
                            scope.passwordLabel = i18n._('Password');
                            scope.sshKeyDataLabel = i18n._('SSH Key');
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
                     scope.authorize = false;
                     scope.authorize_password = null;
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

.factory('FormSave', ['$rootScope', '$location', 'Alert', 'Rest', 'ProcessErrors', 'Empty', 'GetBasePath', 'CredentialForm', 'ReturnToCaller', 'Wait', '$state',
         function ($rootScope, $location, Alert, Rest, ProcessErrors, Empty, GetBasePath, CredentialForm, ReturnToCaller, Wait, $state) {
             return function (params) {
                 var scope = params.scope,
                 mode = params.mode,
                 form = CredentialForm,
                 data = {}, fld, url;

                 for (fld in form.fields) {
                     if (fld !== 'access_key' && fld !== 'secret_key' && fld !== 'ssh_username' &&
                         fld !== 'ssh_password') {
                         if (fld === "organization" && !scope[fld]) {
                             data.user = $rootScope.current_user.id;
                         } else if (scope[fld] === null) {
                             data[fld] = "";
                         } else {
                             data[fld] = scope[fld];
                         }
                     }
                 }

                 data.kind = scope.kind.value;
                 if (scope.become_method === null || typeof scope.become_method === 'undefined') {
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
                         data.username = scope.subscription;
                 }

                 Wait('start');
                 if (mode === 'add') {
                     url = GetBasePath("credentials");
                     Rest.setUrl(url);
                     Rest.post(data)
                     .success(function (data) {
                         scope.addedItem = data.id;

                         // @issue: OLD SEARCH
                        //  Refresh({
                        //      scope: scope,
                        //      set: 'credentials',
                        //      iterator: 'credential',
                        //      url: url
                        //  });

                         Wait('stop');
                         var base = $location.path().replace(/^\//, '').split('/')[0];
                             if (base === 'credentials') {
                             ReturnToCaller();
                         }
                         else {
                             ReturnToCaller(1);
                         }
                         $state.go('credentials.edit', {credential_id: data.id}, {reload: true});

                     })
                     .error(function (data, status) {
                         Wait('stop');
                         // TODO: hopefully this conditional error handling will to away in a future version of tower.  The reason why we cannot
                         // simply pass this error to ProcessErrors is because it will actually match the form element 'ssh_key_unlock' and show
                         // the error there.  The ssh_key_unlock field is not shown when the kind of credential is gce/azure and as a result the
                         // error is never shown.  In the future, the API will hopefully either behave or respond differently.
                         if(status && status === 400 && data && data.ssh_key_unlock && (scope.kind.value === 'gce' || scope.kind.value === 'azure')) {
                             scope.ssh_key_data_api_error = "Encrypted credentials are not supported.";
                         }
                         else {
                             ProcessErrors(scope, data, status, form, {
                                 hdr: 'Error!',
                                 msg: 'Failed to create new Credential. POST status: ' + status
                             });
                         }
                     });
                 } else {
                     url = GetBasePath('credentials') + scope.id + '/';
                     Rest.setUrl(url);
                     Rest.put(data)
                     .success(function () {
                         Wait('stop');
                         $state.go($state.current, {}, {reload: true});
                     })
                     .error(function (data, status) {
                         Wait('stop');
                         ProcessErrors(scope, data, status, form, {
                             hdr: 'Error!',
                             msg: 'Failed to update Credential. PUT status: ' + status
                         });
                     });
                }
             };
         }
]);
