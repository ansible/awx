
function PermissionsList ($scope, $rootScope, $location, $log, $routeParams, Rest, Alert, PermissionList,
                          GenerateList, LoadBreadCrumbs, Prompt, SearchInit, PaginateInit, ReturnToCaller,
                          ClearScope, ProcessErrors, GetBasePath, CheckAccess)
{
    ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                 //scope.
    var list = PermissionList;
    var base = $location.path().replace(/^\//,'').split('/')[0];
    var defaultUrl = GetBasePath(base);
    defaultUrl += ($routeParams['user_id'] !== undefined) ? $routeParams['user_id'] : $routeParams['team_id'];
    defaultUrl += '/permissions/';
    
    var view = GenerateList;
    var scope = view.inject(list, { mode: 'edit' });         // Inject our view
    scope.selected = [];
   
    SearchInit({ scope: scope, set: 'permissions', list: list, url: defaultUrl });
    PaginateInit({ scope: scope, list: list, url: defaultUrl });
    scope.search(list.iterator);

    LoadBreadCrumbs();

    scope.addPermission = function() {
       if (CheckAccess()) {
          $location.path($location.path() + '/add');
       }
       }

    scope.editPermission = function(id) {
       if (CheckAccess()) {
          $location.path($location.path() + '/' + id);
       }
       }
 
    scope.deletePermission = function(id, name) {
       var action = function() {
           var url = GetBasePath('base') + 'permissions/' + id + '/';
           Rest.setUrl(url);
           Rest.destroy()
               .success( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   scope.search(list.iterator);
                   })
               .error( function(data, status, headers, config) {
                   $('#prompt-modal').modal('hide');
                   ProcessErrors(scope, data, status, null,
                      { hdr: 'Error!', msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                   });      
           };
       
       if (checkAccess()) {
           Prompt({ hdr: 'Delete', 
                    body: 'Are you sure you want to delete ' + name + '?',
                    action: action
                    });
       }
       }
}

PermissionsList.$inject = [ '$scope', '$rootScope', '$location', '$log', '$routeParams', 'Rest', 'Alert', 'PermissionList',
                            'GenerateList', 'LoadBreadCrumbs', 'Prompt', 'SearchInit', 'PaginateInit', 'ReturnToCaller',
                            'ClearScope', 'ProcessErrors', 'GetBasePath', 'CheckAccess'
                            ];


function PermissionsAdd ($scope, $rootScope, $compile, $location, $log, $routeParams, PermissionsForm, 
                         GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ClearScope, 
                         GetBasePath, ReturnToCaller, InventoryList, ProjectList, LookUpInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   // Inject dynamic view
   var form = PermissionsForm;
   var generator = GenerateForm;
   var id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var defaultUrl = GetBasePath(base) + id + '/permissions';
   var scope = generator.inject(form, {mode: 'add', related: false});
   var master = {};

   generator.reset();
   LoadBreadCrumbs();
   
   scope['inventoryrequired'] = true;
   scope['projectrequired'] = false;
   scope.category = 'Inventory';
   master.category = 'Inventory';
   master.inventoryrequired = true;
   master.projectrequired = false

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
              ProcessErrors(scope, data, status, PermissionsForm,
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

   scope.selectCategory = function() {
       if (scope.category == 'Inventory') {
          scope.projectrequired = false;
       }
       else {
          scope.projectrequired = true;
       }
       scope.permission_type = null;
       }
}

PermissionsAdd.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'PermissionsForm', 
                           'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ClearScope', 'GetBasePath',
                           'ReturnToCaller', 'InventoryList', 'ProjectList', 'LookUpInit'
                           ];


function PermissionsEdit ($scope, $rootScope, $compile, $location, $log, $routeParams, PermissionsForm, 
                          GenerateForm, Rest, Alert, ProcessErrors, LoadBreadCrumbs, ReturnToCaller, 
                          ClearScope, Prompt, GetBasePath, InventoryList, ProjectList, LookUpInit) 
{
   ClearScope('htmlTemplate');  //Garbage collection. Don't leave behind any listeners/watchers from the prior
                                //scope.

   var generator = GenerateForm;
   var form = PermissionsForm;
   var scope = generator.inject(form, {mode: 'edit', related: true});
   var base_id = ($routeParams.user_id !== undefined) ? $routeParams.user_id : $routeParams.team_id;
   var base = $location.path().replace(/^\//,'').split('/')[0];
   var id = $routeParams.permission_id;
   var defaultUrl = GetBasePath('base') + 'permissions/' + id + '/';
   generator.reset();

   var master = {};
   var relatedSets = {}; 
   

   // Retrieve detail record and prepopulate the form
   Rest.setUrl(defaultUrl); 
   Rest.get()
       .success( function(data, status, headers, config) {
           
           LoadBreadCrumbs({ path: '/users/' + base_id + '/permissions/' + id, title: data.name });

           for (var fld in form.fields) {
              if (data[fld]) {
                 if (form.fields[fld].sourceModel) {
                    var sourceModel = form.fields[fld].sourceModel;
                    var sourceField = form.fields[fld].sourceField;
                    scope[sourceModel + '_' + sourceField] = data.summary_fields[sourceModel][sourceField];
                    master[sourceModel + '_' + sourceField] = data.summary_fields[sourceModel][sourceField];
                 }
                 scope[fld] = data[fld];
                 master[fld] = scope[fld];
              }
           }

           scope.category = 'Deploy';
           if (data['permission_type'] != 'run' && data['permission_type'] != 'check' ) {
              scope.category = 'Inventory';
              scope.projectrequired = false;
           }
           else {
              scope.projectrequired = true;
           }
           master['category'] = scope.category;
           
           LookUpInit({
              scope: scope,
              form: form,
              current_item: data.inventory,
              list: InventoryList, 
              field: 'inventory' 
              });

           LookUpInit({
              scope: scope,
              form: form,
              current_item: data.project,
              list: ProjectList, 
              field: 'project' 
              });
           })
       .error( function(data, status, headers, config) {
           ProcessErrors(scope, data, status, form,
               { hdr: 'Error!', msg: 'Failed to retrieve Permission: ' + id + '. GET status: ' + status });
           });


   // Save changes to the parent
   scope.formSave = function() {
      var data = {}
      for (var fld in form.fields) {
          data[fld] = scope[fld];   
      } 
      Rest.setUrl(defaultUrl);
      Rest.put(data)
          .success( function(data, status, headers, config) {
              ReturnToCaller(1);
              })
          .error( function(data, status, headers, config) {
              ProcessErrors(scope, data, status, form,
                  { hdr: 'Error!', msg: 'Failed to update Permission: ' + $routeParams.id + '. PUT status: ' + status });
              });
      };


   // Cancel
   scope.formReset = function() {
      generator.reset();
      for (var fld in master) {
          scope[fld] = master[fld];
      }
      };


   scope.selectCategory = function() {
       if (scope.category == 'Inventory') {
          scope.projectrequired = false;
       }
       else {
          scope.projectrequired = true;
       }
       scope.permission_type = null;
       }

}

PermissionsEdit.$inject = [ '$scope', '$rootScope', '$compile', '$location', '$log', '$routeParams', 'PermissionsForm', 
                            'GenerateForm', 'Rest', 'Alert', 'ProcessErrors', 'LoadBreadCrumbs', 'ReturnToCaller', 
                            'ClearScope', 'Prompt', 'GetBasePath', 'InventoryList', 'ProjectList', 'LookUpInit'
                            ]; 
  
