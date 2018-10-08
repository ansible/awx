/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default [
     '$scope',
     '$rootScope',
     'ConfigurationUiForm',
     'CreateSelect2',
     'GenerateForm',
     'i18n',
     '$stateParams',
     function(
        $scope,
        $rootScope,
        ConfigurationUiForm,
        CreateSelect2,
        GenerateForm,
        i18n,
        $stateParams
     ) {
         var generator = GenerateForm;
         var form = ConfigurationUiForm;

         const formTracker = $scope.$parent.vm.formTracker;
         if ($stateParams.form === 'ui') {
            formTracker.setCurrentAuth('ui'); 
         }

         var keys = _.keys(form.fields);
         _.each(keys, function(key) {
             if($scope.configDataResolve[key].type === 'choice') {
                 // Create options for dropdowns
                 var optionsGroup = key + '_options';
                 $scope.$parent.$parent[optionsGroup] = [];
                 _.each($scope.configDataResolve[key].choices, function(choice){
                     $scope.$parent.$parent[optionsGroup].push({
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
                 awPopOver: ($scope.configDataResolve[key].defined_in_file) ?
                     null: $scope.configDataResolve[key].help_text,
                 label: $scope.configDataResolve[key].label,
                 name: key,
                 toggleSource: key,
                 dataPlacement: 'top',
                 dataTitle: $scope.configDataResolve[key].label,
                 required: $scope.configDataResolve[key].required,
                 ngDisabled: $rootScope.user_is_system_auditor,
                 disabled: $scope.configDataResolve[key].disabled || null,
                 readonly: $scope.configDataResolve[key].readonly || null,
                 definedInFile: $scope.configDataResolve[key].defined_in_file || null
             });
         }

         generator.inject(form, {
             id: 'configure-ui-form',
             mode: 'edit',
             scope: $scope.$parent.$parent,
             related: true,
             noPanel: true
         });

         // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
         var dropdownRendered = false;

         function populatePendoTrackingState(flag){
             if($scope.$parent.$parent.PENDO_TRACKING_STATE !== null) {
                 $scope.$parent.$parent.PENDO_TRACKING_STATE = _.find($scope.$parent.$parent.PENDO_TRACKING_STATE_options, { value: $scope.$parent.$parent.PENDO_TRACKING_STATE });
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
     }
 ];
