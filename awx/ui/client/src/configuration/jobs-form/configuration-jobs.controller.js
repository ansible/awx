/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default [
    '$scope',
    '$rootScope',
    '$state',
    '$stateParams',
    '$timeout',
    'ConfigurationJobsForm',
    'ConfigurationService',
    'ConfigurationUtils',
    'CreateSelect2',
    'GenerateForm',
    'ParseTypeChange',
    'i18n',
    function(
        $scope,
        $rootScope,
        $state,
        $stateParams,
        $timeout,
        ConfigurationJobsForm,
        ConfigurationService,
        ConfigurationUtils,
        CreateSelect2,
        GenerateForm,
        ParseTypeChange,
        i18n
    ) {
        var generator = GenerateForm;
        var form = ConfigurationJobsForm;

        let tab;
        let codeInputInitialized = false;

        $scope.$parent.AD_HOC_COMMANDS_options = [];
        _.each($scope.$parent.configDataResolve.AD_HOC_COMMANDS.default, function(command) {
            $scope.$parent.AD_HOC_COMMANDS_options.push({
                name: command,
                label: command,
                value: command
            });
        });

        // Disable the save button for system auditors
        form.buttons.save.disabled = $rootScope.user_is_system_auditor;

        var keys = _.keys(form.fields);
        _.each(keys, function(key) {
            addFieldInfo(form, key);
        });

        function addFieldInfo(form, key) {
            _.extend(form.fields[key], {
                awPopOver: ($scope.$parent.configDataResolve[key].defined_in_file) ?
                    null: $scope.$parent.configDataResolve[key].help_text,
                label: $scope.$parent.configDataResolve[key].label,
                name: key,
                toggleSource: key,
                dataPlacement: 'top',
                dataTitle: $scope.$parent.configDataResolve[key].label,
                required: $scope.$parent.configDataResolve[key].required,
                ngDisabled: $rootScope.user_is_system_auditor,
                disabled: $scope.$parent.configDataResolve[key].disabled || null,
                readonly: $scope.$parent.configDataResolve[key].readonly || null,
                definedInFile: $scope.$parent.configDataResolve[key].defined_in_file || null
            });
        }

        generator.inject(form, {
            id: 'configure-jobs-form',
            mode: 'edit',
            scope: $scope.$parent,
            related: false,
            noPanel: true
        });

        function initializeCodeInput () {
            let name = 'AWX_TASK_ENV';

            ParseTypeChange({
               scope: $scope.$parent,
               variable: name,
               parseType: 'application/json',
               field_id: `configuration_jobs_template_${name}`
             });

            $scope.parseTypeChange('parseType', name);
        }

        function loadAdHocCommands () {
            $scope.$parent.AD_HOC_COMMANDS_values = $scope.$parent.AD_HOC_COMMANDS.map(value => value);
            $scope.$parent.AD_HOC_COMMANDS = $scope.$parent.AD_HOC_COMMANDS.map(value => ({
                value,
                name: value,
                label: value
            }));

            $scope.$parent.AD_HOC_COMMANDS_options = $scope.$parent.AD_HOC_COMMANDS.map(tag => tag);

            CreateSelect2({
                element: '#configuration_jobs_template_AD_HOC_COMMANDS',
                multiple: true,
                addNew: true,
                placeholder: i18n._('Select commands')
            });

        }

        function revertAdHocCommands () {
            $scope.$parent.AD_HOC_COMMANDS = $scope.$parent.configDataResolve.AD_HOC_COMMANDS.default.map(value => ({
                value,
                name: value,
                label: value
            }));

            $('.select2-selection__choice').each(function(i, element){
                if(!_.contains($scope.$parent.configDataResolve.AD_HOC_COMMANDS.default, element.title)){
                    $(`#configuration_jobs_template_AD_HOC_COMMANDS option[value='${element.title}']`).remove();
                    element.remove();
                }
            });

            $scope.$parent.AD_HOC_COMMANDS_options = $scope.$parent.AD_HOC_COMMANDS.map(tag => tag);
            $scope.$parent.AD_HOC_COMMANDS_values = $scope.$parent.AD_HOC_COMMANDS.map(tag => tag.value);
            CreateSelect2({
                element: '#configuration_jobs_template_AD_HOC_COMMANDS',
                multiple: true,
                addNew: true,
                placeholder: i18n._('Select commands'),
                options: $scope.$parent.AD_HOC_COMMANDS_options
            });

        }

        // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
        // TODO Find better solution for this bug
        $timeout(function(){
            $scope.$parent.configuration_jobs_template_form.$setPristine();
        }, 1000);


        // Managing the state of select2's tags since the behavior is unpredictable otherwise.
        let commandsElement = $('#configuration_jobs_template_AD_HOC_COMMANDS');

        commandsElement.on('select2:select', event => {
            let command = event.params.data.text;
            let commands = $scope.$parent.AD_HOC_COMMANDS_values;

            commands.push(command);
        });

        commandsElement.on('select2:unselect', event => {
            let command = event.params.data.text;
            let commands = $scope.$parent.AD_HOC_COMMANDS_values;

            $scope.$parent.AD_HOC_COMMANDS_values = commands.filter(value => value !== command);
        });

        $scope.$on('AD_HOC_COMMANDS_reverted', () => revertAdHocCommands());

        /*
         * Controllers for each tab are initialized when configuration is opened. A listener
         * on the URL itself is necessary to determine which tab is active. If a non-active
         * tab initializes a codemirror, it doesn't display properly until the user navigates
         * to the tab and it's been clicked.
         */
        $scope.$on('$locationChangeStart', (event, url) => {
            let parts = url.split('/');
            tab = parts[parts.length - 1];

            if (tab === 'jobs' && !codeInputInitialized) {
                initializeCodeInput();
                codeInputInitialized = true;
            }
        });

        /*
         * Necessary to listen for revert clicks and relaunch the codemirror instance.
         */
        $scope.$on('codeMirror_populated', () => {
            if (tab === 'jobs') {
                initializeCodeInput();
            }
        });

        /*
         * This event is fired if the user navigates directly to this tab, where the
         * $locationChangeStart does not. Watching this and location ensure proper display on
         * direct load of this tab or if the user comes from a different tab.
         */
        $scope.$on('populated', () => {
            tab = $stateParams.currentTab;

            if (tab === 'jobs') {
                initializeCodeInput();
                codeInputInitialized = true;
            }

            loadAdHocCommands();
        });
    }
];
