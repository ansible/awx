/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default [
     '$scope',
     '$rootScope',
     '$state',
     '$timeout',
     'ConfigurationUiForm',
     'ConfigurationService',
     'CreateSelect2',
     'GenerateForm',
     'i18n',
     function(
        $scope,
        $rootScope,
        $state,
        $timeout,
        ConfigurationUiForm,
        ConfigurationService,
        CreateSelect2,
        GenerateForm,
        i18n
     ) {
         var uiVm = this;
         var generator = GenerateForm;
         var form = ConfigurationUiForm;


         var keys = _.keys(form.fields);
         _.each(keys, function(key) {
             if($scope.$parent.configDataResolve[key].type === 'choice') {
                 // Create options for dropdowns
                 var optionsGroup = key + '_options';
                 $scope.$parent[optionsGroup] = [];
                 _.each($scope.$parent.configDataResolve[key].choices, function(choice){
                     $scope.$parent[optionsGroup].push({
                         name: choice[0],
                         label: choice[1],
                         value: choice[0]
                     });
                 });
             }
             addFieldInfo(form, key);
         });

         // Disable the save button for system auditors
         form.buttons.save.disabled = $rootScope.user_is_system_auditor;

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
             id: 'configure-ui-form',
             mode: 'edit',
             scope: $scope.$parent,
             related: true,
             noPanel: true
         });

         // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
         var dropdownRendered = false;

         function populatePendoTrackingState(flag){
             if($scope.$parent.PENDO_TRACKING_STATE !== null) {
                 $scope.$parent.PENDO_TRACKING_STATE = _.find($scope.$parent.PENDO_TRACKING_STATE_options, { value: $scope.$parent.PENDO_TRACKING_STATE });
             }

             if(flag !== undefined){
                 dropdownRendered = flag;
             }

             if(!dropdownRendered) {
                 dropdownRendered = true;
                 CreateSelect2({
                     element: '#configuration_ui_template_PENDO_TRACKING_STATE',
                     multiple: false,
                     placeholder: i18n._('Select commands')
                 });
             }
         }

         $scope.$on('PENDO_TRACKING_STATE_populated', function(e, data, flag) {
             populatePendoTrackingState(flag);
         });

         $scope.$on('populated', function(){
             populatePendoTrackingState(false);
         });

         angular.extend(uiVm, {

         });

     }
 ];
