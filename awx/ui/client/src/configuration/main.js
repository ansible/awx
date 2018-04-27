/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import configurationService from './configuration.service';
import ConfigurationUtils from './configurationUtils.service';
import configurationRoute from './configuration.route';
import licenseRoute from './license.route';
import configurationController from './configuration.controller.js';

// Import forms
//authorization sub-forms
import configurationAzureForm from './auth-form/sub-forms/auth-azure.form.js';
import configurationGithubForm from './auth-form/sub-forms/auth-github.form.js';
import configurationGithubOrgForm from './auth-form/sub-forms/auth-github-org.form';
import configurationGithubTeamForm from './auth-form/sub-forms/auth-github-team.form';
import configurationGoogleForm from './auth-form/sub-forms/auth-google-oauth2.form';
import configurationLdapForm from './auth-form/sub-forms/auth-ldap.form.js';
import configurationLdap1Form from './auth-form/sub-forms/auth-ldap1.form.js';
import configurationLdap2Form from './auth-form/sub-forms/auth-ldap2.form.js';
import configurationLdap3Form from './auth-form/sub-forms/auth-ldap3.form.js';
import configurationLdap4Form from './auth-form/sub-forms/auth-ldap4.form.js';
import configurationLdap5Form from './auth-form/sub-forms/auth-ldap5.form.js';
import configurationRadiusForm from './auth-form/sub-forms/auth-radius.form.js';
import configurationTacacsForm from './auth-form/sub-forms/auth-tacacs.form.js';
import configurationSamlForm from './auth-form/sub-forms/auth-saml.form';

//system sub-forms
import systemActivityStreamForm from './system-form/sub-forms/system-activity-stream.form.js';
import systemLoggingForm from './system-form/sub-forms/system-logging.form.js';
import systemMiscForm from './system-form/sub-forms/system-misc.form.js';

import configurationJobsForm from './jobs-form/configuration-jobs.form';
import configurationUiForm from './ui-form/configuration-ui.form';

export default
angular.module('configuration', [])
    .controller('ConfigurationController', configurationController)
    //auth forms
    .factory('configurationAzureForm', configurationAzureForm)
    .factory('configurationGithubForm', configurationGithubForm)
    .factory('configurationGithubOrgForm', configurationGithubOrgForm)
    .factory('configurationGithubTeamForm', configurationGithubTeamForm)
    .factory('configurationGoogleForm', configurationGoogleForm)
    .factory('configurationLdapForm', configurationLdapForm)
    .factory('configurationLdap1Form', configurationLdap1Form)
    .factory('configurationLdap2Form', configurationLdap2Form)
    .factory('configurationLdap3Form', configurationLdap3Form)
    .factory('configurationLdap4Form', configurationLdap4Form)
    .factory('configurationLdap5Form', configurationLdap5Form)
    .factory('configurationRadiusForm', configurationRadiusForm)
    .factory('configurationTacacsForm', configurationTacacsForm)
    .factory('configurationSamlForm', configurationSamlForm)
    //system forms
    .factory('systemActivityStreamForm', systemActivityStreamForm)
    .factory('systemLoggingForm', systemLoggingForm)
    .factory('systemMiscForm', systemMiscForm)

    //other forms
    .factory('ConfigurationJobsForm', configurationJobsForm)
    .factory('ConfigurationUiForm', configurationUiForm)

    //helpers and services
    .factory('ConfigurationUtils', ConfigurationUtils)
    .service('ConfigurationService', configurationService)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(configurationRoute);
        $stateExtender.addState(licenseRoute);
    }]);
