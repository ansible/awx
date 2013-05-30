/************************************
 *
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Utility functions
 *
 */
angular.module('Utilities',[])
   
   .factory('ClearScope', function() {
      return function(id) {
      var element = document.getElementById(id);
      var scope = angular.element(element).scope();
      scope.$destroy();  
      }
   })

   .factory('ToggleClass', function() {
      return function(selector, cssClass) {
      // Toggles the existance of a css class on a given element   
      if ( $(selector) && $(selector).hasClass(cssClass) ) {
         $(selector).removeClass(cssClass);
      }
      else if ($(selector)) {
         $(selector).addClass(cssClass);
      }
      } 
   })

   .factory('Alert', ['$rootScope', function($rootScope) {
      return function(hdr, msg) {
      // Pass in the header and message you want displayed on TB modal dialog found in index.html.
      // Assumes an id of 'alert-modal'
      $rootScope.alertHeader = hdr;
      $rootScope.alertBody = msg;
      $('#alert-modal').modal({ show: true, keyboard: true,  backdrop: 'static' });
      }
   }])

   .factory('ProcessErrors', ['$log', 'Alert', function($log, Alert) {
      return function(scope, data, status, form, defaultMsg) {
      if (status == 403) {
         Alert('Access Denied', 'The API responded with a 403 Access Denied error. You do not have permission to perform the ' +
               'requested action. Please contact a system administrator.');
      }
      else if (data.non_field_errors) {
         Alert('Error!', data.non_field_errors);
      }
      else if (data.detail) {
         Alert(defaultMsg.hdr, defaultMsg.msg + ' ' + data.detail);
      }
      else if (data['__all__']) {
         Alert('Error!', data['__all__']);
      }
      else if (form) {
         var fieldErrors = false; 
         for (var field in form.fields ) {
             if (data[field]) {
                scope[field + '_api_error'] = data[field][0];
                fieldErrors = true;
             }
         }
         if ( (!fieldErrors) && defaultMsg) {
            Alert(defaultMsg.hdr, defaultMsg.msg);
         }
      }
      else {
         Alert(defaultMsg.hdr, defaultMsg.msg); 
      }
      }
   }])

   .factory('LoadBreadCrumbs', ['$rootScope', '$routeParams', '$location', function($rootScope, $routeParams, $location, Rest) {
      return function(crumb) {
      
      //Keep a list of path/title mappings. When we see /organizations/XX in the path, for example, 
      //we'll know the actual organization name it maps to.
      if (crumb !== null && crumb !== undefined) {
         var found = false; 
         for (var i=0; i < $rootScope.crumbCache.length; i++) {
             if ($rootScope.crumbCache[i].path == crumb.path) {
                found = true; 
                $rootScope.crumbCache[i] = crumb;
                break;     
             }
         }
         if (found == false) {
            $rootScope.crumbCache.push(crumb);
         }
      }

      var paths = $location.path().replace(/^\//,'').split('/');
      var ppath = '';
      $rootScope.breadcrumbs = [];
      if (paths.length > 1) {
         var parent, child;
         for (var i=0; i < paths.length - 1; i++) {
            if (i > 0 && paths[i].match(/\d+/)) {
               parent = paths[i-1];
               if (parent == 'inventories') {
                  child = 'inventory';
               }
               else {
                  child = parent.substring(0,parent.length - 1);  //assumes parent ends with 's'
               }
               // find the correct title
               for (var j=0; j < $rootScope.crumbCache.length; j++) {
                   if ($rootScope.crumbCache[j].path == '/' + parent + '/' + paths[i]) {
                      child = $rootScope.crumbCache[j].title;
                      break;
                   }
               }
               $rootScope.breadcrumbs.push({ title: child, path: ppath + '/' + paths[i] });
            }
            else {
               $rootScope.breadcrumbs.push({ title: paths[i], path: ppath + '/' + paths[i] });
            }
            ppath += '/' + paths[i];
         }
      }
      }
   }])

   .factory('ReturnToCaller', ['$location', function($location) {
      return function(idx) {
      // Split the current path by '/' and use the array elements from 0 up to and
      // including idx as the new path.  If no idx value supplied, use 0 to length - 1.  
      
      var paths = $location.path().replace(/^\//,'').split('/');
      var newpath = ''; 
      idx = (idx == null || idx == undefined) ? paths.length - 1 : idx + 1;
      for (var i=0; i < idx; i++) {
          newpath += '/' + paths[i] 
      }
      $location.path(newpath);
      }
   }]);