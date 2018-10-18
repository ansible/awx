/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import settingsService from './settings.service';
import settingsUtils from './settingsUtils.service';

// Import forms
//authorization sub-forms
import configurationAzureForm from './forms/auth-form/sub-forms/auth-azure.form.js';
import configurationGithubForm from './forms/auth-form/sub-forms/auth-github.form.js';
import configurationGithubOrgForm from './forms/auth-form/sub-forms/auth-github-org.form';
import configurationGithubTeamForm from './forms/auth-form/sub-forms/auth-github-team.form';
import configurationGoogleForm from './forms/auth-form/sub-forms/auth-google-oauth2.form';
import configurationLdapForm from './forms/auth-form/sub-forms/auth-ldap.form.js';
import configurationLdap1Form from './forms/auth-form/sub-forms/auth-ldap1.form.js';
import configurationLdap2Form from './forms/auth-form/sub-forms/auth-ldap2.form.js';
import configurationLdap3Form from './forms/auth-form/sub-forms/auth-ldap3.form.js';
import configurationLdap4Form from './forms/auth-form/sub-forms/auth-ldap4.form.js';
import configurationLdap5Form from './forms/auth-form/sub-forms/auth-ldap5.form.js';
import configurationRadiusForm from './forms/auth-form/sub-forms/auth-radius.form.js';
import configurationTacacsForm from './forms/auth-form/sub-forms/auth-tacacs.form.js';
import configurationSamlForm from './forms/auth-form/sub-forms/auth-saml.form';

//system sub-forms
import systemActivityStreamForm from './forms/system-form/sub-forms/system-activity-stream.form.js';
import systemLoggingForm from './forms/system-form/sub-forms/system-logging.form.js';
import systemMiscForm from './forms/system-form/sub-forms/system-misc.form.js';

import configurationJobsForm from './forms/jobs-form/configuration-jobs.form';
import configurationUiForm from './forms/ui-form/configuration-ui.form';

// Wrapper form route
import settingsFormRoute from './forms/settings-form.route';

import settingsRoute from './settings.route';
import settingsController from './settings.controller.js';

export default
angular.module('configuration', [])
    .controller('SettingsController', settingsController)
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
    .factory('SettingsUtils', settingsUtils)
    .service('SettingsService', settingsService)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(settingsFormRoute);
        $stateExtender.addState(settingsRoute);
    }]);
