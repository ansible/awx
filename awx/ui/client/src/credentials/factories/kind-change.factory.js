export default
    function KindChange(Empty, i18n) {
        return function(params) {
            var scope = params.scope,
            reset = params.reset;

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
            scope.key_description = i18n.sprintf(i18n._("Paste the contents of the SSH private key file.%s or click to close%s"), "<div class=\"popover-footer\"><span class=\"key\">Esc</span>", "</div>");
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
            scope.projectPopOver = "<p>" + i18n._("The project value") + "</p>";
            scope.hostPopOver = "<p>" + i18n._("The host value") + "</p>";
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
                        scope.projectPopOver = "<p>" + i18n._("The Project ID is the " +
                        "GCE assigned identification. It is constructed as " +
                        "two words followed by a three digit number.  Such " +
                        "as: ") + "</p><p>adjective-noun-000</p>";
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
                        scope.projectPopOver = "<p>" + i18n._("This is the tenant name. " +
                            " This value is usually the same " +
                            " as the username.") + "</p>";
                        scope.hostPopOver = "<p>" + i18n._("The host to authenticate with.") +
                            "<br />" + i18n.sprintf(i18n._("For example, %s"), "https://openstack.business.com/v2.0/");
                    break;
                    case 'satellite6':
                       scope.username_required = true;
                       scope.password_required = true;
                       scope.passwordLabel = i18n._('Password');
                       scope.host_required = true;
                       scope.hostLabel = i18n._("Satellite 6 URL");
                       scope.hostPopOver = i18n.sprintf(i18n._("Enter the URL which corresponds to your %s" +
                           "Red Hat Satellite 6 server. %s" +
                           "For example, %s"), "<br />", "<br />", "https://satellite.example.org");
                    break;
                    case 'cloudforms':
                       scope.username_required = true;
                       scope.password_required = true;
                       scope.passwordLabel = i18n._('Password');
                       scope.host_required = true;
                       scope.hostLabel = i18n._("CloudForms URL");
                       scope.hostPopOver = i18n.sprintf(i18n._("Enter the URL for the virtual machine which %s" +
                           "corresponds to your CloudForms instance. %s" +
                           "For example, %s"), "<br />", "<br />", "https://cloudforms.example.org");
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
        };
    }

KindChange.$inject =
    [   'Empty', 'i18n'   ];
