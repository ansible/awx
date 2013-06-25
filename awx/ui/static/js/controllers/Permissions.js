function PermissionsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, PermissionsForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, 
                         GetBasePath, ReturnToCaller, InventoryList, ProjectList, LookUpInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = PermissionsForm;
   var generator = GenerateForm;
   var id = $routeParams.user_id;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath(base) + id + '/permissions';
   var scope = generator.inject(form, {mode: 'add', related: false});
   var master = {};

   generator.reset();
   LoadBreadCrumbs();
   
   scope.category = 'i';
   master.category = 'i';

   LookUpInit({
      scope: scope,
      form: form,
      current_item: null,
      list: InventoryList, 
      field: 'inventory' 
      });

   LookUpInit({
      scope: scope,
      form: form,
      current_item: null,
      list: ProjectList, 
      field: 'project' 
      });

   // Save
   scope.formSave = function() {
      var data = {};
      for (var fld in form.fields) {
          data[fld] = scope[fld];
      }
      var url = (base == 'teams') ? GetBasePath('teams') + id + '/permissions/' : GetBasePath('users') + id + '/permissions/';
      Rest.setUrl(url);
      Rest.post(data)
          .success( function(data, status, headers, config) {
              ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, ProjectsForm,
                  { hdr: 'Error!', msg: 'Failed to create new permission. Post returned status: ' + status });
              });
      };

   // Cancel
   scope.formReset = function() {
      $rootScope.flashMessage = null;
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      }; 
}

ProjectsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'PermissionForm', 
                        'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                        'ReturnToCaller', 'InventoryList', 'ProjectList', 'LookUpInit'
                        ];


