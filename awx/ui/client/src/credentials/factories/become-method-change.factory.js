export default
    function BecomeMethodChange(Empty, i18n) {
        return function(params) {
           var scope = params.scope;

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
        };
    }

BecomeMethodChange.$inject =
    [   'Empty', 'i18n'   ];
