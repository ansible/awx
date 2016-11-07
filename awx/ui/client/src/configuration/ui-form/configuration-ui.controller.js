/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

 export default [
     '$scope',
     '$state',
     '$timeout',
     'ConfigurationUiForm',
     'ConfigurationService',
     'CreateSelect2',
     'GenerateForm',
     function(
        $scope,
        $state,
        $timeout,
        ConfigurationUiForm,
        ConfigurationService,
        CreateSelect2,
        GenerateForm
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

         function addFieldInfo(form, key) {
             _.extend(form.fields[key], {
                 awPopOver: $scope.$parent.configDataResolve[key].help_text,
                 label: $scope.$parent.configDataResolve[key].label,
                 name: key,
                 toggleSource: key,
                 dataPlacement: 'top',
                 dataTitle: $scope.$parent.configDataResolve[key].label
             });
         }

         generator.inject(form, {
             id: 'configure-ui-form',
             mode: 'edit',
             scope: $scope.$parent,
             related: true
         });

         // Flag to avoid re-rendering and breaking Select2 dropdowns on tab switching
         var dropdownRendered = false;

         $scope.$on('populated', function(){
             if(!dropdownRendered) {
                 dropdownRendered = true;
                 CreateSelect2({
                     element: '#configuration_ui_template_PENDO_TRACKING_STATE',
                     multiple: false,
                     placeholder: 'Select commands',
                     opts: [{
                         id: $scope.$parent.PENDO_TRACKING_STATE,
                         text: $scope.$parent.PENDO_TRACKING_STATE
                     }]
                 });
                 // Fix for bug where adding selected opts causes form to be $dirty and triggering modal
                 // TODO Find better solution for this bug
                 $timeout(function(){
                     $scope.$parent.configuration_ui_template_form.$setPristine();
                 }, 1000);
             }
         });

         angular.extend(uiVm, {

         });

     }
 ];
