import {templateUrl} from '../../shared/template-url/template-url.factory';
import { N_ } from '../../i18n';
import SettingsFormController from './settings-form.controller';

// Import form controllers
import SettingsAuthController from './auth-form/configuration-auth.controller';
import SettingsJobsController from './jobs-form/configuration-jobs.controller';
import SettingsSystemController from './system-form/configuration-system.controller';
import SettingsUiController from './ui-form/configuration-ui.controller';

export default {
    name: 'settings.form',
    route: '/:form',
    ncyBreadcrumb: {
        label: N_("{{ vm.getCurrentFormTitle() }}")
    },
    views: {
        '@': {
            templateUrl: templateUrl('configuration/forms/settings-form'),
            controller: SettingsFormController,
            controllerAs: 'vm'
        },
        'auth@settings.form': {
            templateUrl: templateUrl('configuration/forms/auth-form/configuration-auth'),
            controller: SettingsAuthController,
            controllerAs: 'authVm'
        },
        'jobs@settings.form': {
            templateUrl: templateUrl('configuration/forms/jobs-form/configuration-jobs'),
            controller: SettingsJobsController,
            controllerAs: 'jobsVm'
        },
        'system@settings.form': {
            templateUrl: templateUrl('configuration/forms/system-form/configuration-system'),
            controller: SettingsSystemController,
            controllerAs: 'systemVm'
        },
        'ui@settings.form': {
            templateUrl: templateUrl('configuration/forms/ui-form/configuration-ui'),
            controller: SettingsUiController,
            controllerAs: 'uiVm'
        },
        'license@settings.form': {
            templateUrl: templateUrl('license/license'),
            controller: 'licenseController'
        },
    },
    onEnter: ['$state', 'ConfigService', '$stateParams', (state, configService, stateParams) => {
        return configService.getConfig()
            .then(config => {
                if (_.get(config, 'license_info.license_type') === 'open' && stateParams.form === 'license') {
                    return state.go('settings');
                }
            });
    }],
    resolve: {
        subscriptionCreds: ['Rest', 'GetBasePath', function(Rest, GetBasePath) {
            Rest.setUrl(`${GetBasePath('settings')}system/`);
            return Rest.get()
                .then(({data}) => {
                    const subscriptionCreds = {};
                    if (data.SUBSCRIPTIONS_USERNAME && data.SUBSCRIPTIONS_USERNAME !== "") {
                        subscriptionCreds.SUBSCRIPTIONS_USERNAME = data.SUBSCRIPTIONS_USERNAME;
                    }

                    if (data.SUBSCRIPTIONS_PASSWORD && data.SUBSCRIPTIONS_PASSWORD !== "") {
                        subscriptionCreds.SUBSCRIPTIONS_PASSWORD = data.SUBSCRIPTIONS_PASSWORD;
                    }
                    
                    return subscriptionCreds;
                }).catch(() => {
                        return {};
                });
        }]
    }
};