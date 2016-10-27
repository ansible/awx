/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

import configurationService from './configuration.service';
import ConfigurationUtils from './configurationUtils.service';
import configurationRoute from './configuration.route';
import configurationController from './configuration.controller.js';

// Import forms
//authorization sub-forms
import configurationGithubForm from './auth-form/sub-forms/auth-github.form.js';
import configurationGithubOrgForm from './auth-form/sub-forms/auth-github-org.form';
import configurationGithubTeamForm from './auth-form/sub-forms/auth-github-team.form';
import configurationGoogleForm from './auth-form/sub-forms/auth-google-oauth2.form';
import configurationLdapForm from './auth-form/sub-forms/auth-ldap.form.js';
import configurationRadiusForm from './auth-form/sub-forms/auth-radius.form.js';
import configurationSamlForm from './auth-form/sub-forms/auth-saml.form';

import configurationJobsForm from './jobs-form/configuration-jobs.form';
import configurationSystemForm from './system-form/configuration-system.form';
import configurationUiForm from './ui-form/configuration-ui.form';

export default
angular.module('configuration', [])
    .controller('ConfigurationController', configurationController)
    //auth forms
    .factory('configurationGithubForm', configurationGithubForm)
    .factory('configurationGithubOrgForm', configurationGithubOrgForm)
    .factory('configurationGithubTeamForm', configurationGithubTeamForm)
    .factory('configurationGoogleForm', configurationGoogleForm)
    .factory('configurationLdapForm', configurationLdapForm)
    .factory('configurationRadiusForm', configurationRadiusForm)
    .factory('configurationSamlForm', configurationSamlForm)
    .factory('ConfigurationJobsForm', configurationJobsForm)
    .factory('ConfigurationSystemForm', configurationSystemForm)
    .factory('ConfigurationUiForm', configurationUiForm)
    .factory('ConfigurationUtils', ConfigurationUtils)
    .service('ConfigurationService', configurationService)
    .run(['$stateExtender', function($stateExtender) {
        $stateExtender.addState(configurationRoute);
    }]);
