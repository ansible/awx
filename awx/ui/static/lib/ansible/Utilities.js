/************************************
 *
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Utility functions
 *
 */
angular.module('Utilities',['RestServices'])
   
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

   .factory('Alert', ['$rootScope', '$location', function($rootScope, $location) {
   return function(hdr, msg, cls, action, secondAlert, disableButtons) {
       // Pass in the header and message you want displayed on TB modal dialog found in index.html.
       // Assumes an #id of 'alert-modal'. Pass in an optional TB alert class (i.e. alert-danger, alert-success,
       // alert-info...). Pass an optional function(){}, if you want a specific action to occur when user
       // clicks 'OK' button. Set secondAlert to true, when a second dialog is needed.
       if (secondAlert) {
          $rootScope.alertHeader2 = hdr;
          $rootScope.alertBody2 = msg;
          $rootScope.alertClass2 = (cls) ? cls : 'alert-danger';  //default alert class is alert-danger
          $('#alert-modal2').modal({ show: true, keyboard: true , backdrop: 'static' });
          $rootScope.disableButtons2 = (disableButtons) ? true : false;
          if (action) {
             $('#alert-modal2').on('hidden', function() {
                 action();
                 });
          }
          $(document).bind('keydown', function(e) {
             if (e.keyCode === 27) {
                $('#alert-modal2').modal('hide');
                if (action) {
                   action();
                }
             }
             });
       }
       else {
          $rootScope.alertHeader = hdr;
          $rootScope.alertBody = msg;
          $rootScope.alertClass = (cls) ? cls : 'alert-danger';  //default alert class is alert-danger
          $('#alert-modal').modal({ show: true, keyboard: true , backdrop: 'static' });
         
          $(document).bind('keydown', function(e) {
              if (e.keyCode === 27) {
                 $('#alert-modal').modal('hide');
                 if (action) {
                    action();
                 }
              }
              });

          $rootScope.disableButtons = (disableButtons) ? true : false;
          if (action) {
             $('#alert-modal').on('hidden', function() {
                 action();
                 });
          }
       }
       }
       }])

   .factory('ProcessErrors', ['$cookieStore', '$log', '$location', '$rootScope', 'Alert',
   function($cookieStore, $log, $location, $rootScope, Alert) {
   return function(scope, data, status, form, defaultMsg) {
       if ($AnsibleConfig.debug_mode && console) {
          console.log('Debug status: ' + status);
          console.log('Debug data: ');
          console.log(data);
       }
       if (status == 403) {
          var msg = 'The API responded with a 403 Access Denied error. ';
          if (data['detail']) {
             msg += 'Detail: ' + data['detail'];
          }
          else {
             msg += 'Please contact your system administrator.';
          }
          Alert(defaultMsg.hdr, msg);
       }
       else if (status == 401 && data.detail && data.detail == 'Token is expired') {
          $rootScope.sessionExpired = true;
          $cookieStore.put('sessionExpired', true);
          $location.path('/login');
       }
       else if (status == 401 && data.detail && data.detail == 'Invalid token') {
          // should this condition be treated as an expired session?? Yes, for now.
          $rootScope.sessionExpired = true;
          $cookieStore.put('sessionExpired', true);
          $location.path('/login');
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
              if (form.fields[field].realName) {
                 if (data[form.fields[field].realName]) {
                    scope[field + '_api_error'] = data[form.fields[field]][0];
                    fieldErrors = true;
                 }
              }
              if (form.fields[field].sourceModel) {
                 if (data[field]) {
                    scope[form.fields[field].sourceModel + '_' + form.fields[field].sourceField + '_api_error'] = 
                        data[field][0];
                    fieldErrors = true;
                 }
              }
              else {
                 if (data[field]) {
                    scope[field + '_api_error'] = data[field][0];
                    fieldErrors = true;
                 }
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
                if ($rootScope.crumbCache[j] && $rootScope.crumbCache[j]['altPath'] !== undefined) {
                   // Use altPath to override default path construction
                   $rootScope.breadcrumbs.push({ title: child, path: $rootScope.crumbCache[j].altPath });
                }
                else { 
                   if (paths[i - 1] == 'hosts') {
                      // For hosts, there is no /hosts, so we need to link back to the inventory
                      // We end up here when user has clicked refresh and the crumbcache is missing
                      $rootScope.breadcrumbs.push({ title: child, 
                          path: '/inventories/' + $routeParams.inventory + '/hosts' });
                   }
                   else { 
                      $rootScope.breadcrumbs.push({ title: child, path: ppath + '/' + paths[i] });
                   }
                }
             }
             else {
                if (paths[i] == 'hosts') {
                   $rootScope.breadcrumbs.push({ title: paths[i], path: '/inventories/' + $routeParams.inventory +
                       '/hosts' });
                }
                else {
                   $rootScope.breadcrumbs.push({ title: paths[i], path: ppath + '/' + paths[i] });
                }
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
       }])

   .factory('FormatDate', [ function() {
   return function(dt) {
       var result = ('0' + (dt.getMonth() + 1)).slice(-2) + '/';
       result += ('0' + dt.getDate()).slice(-2) + '/';
       result += ('0' + (dt.getFullYear() - 2000)).slice(-2) + ' ';
       result += ('0' + dt.getHours()).slice(-2) + ':';
       result += ('0' + dt.getMinutes()).slice(-2) + ':';
       result += ('0' + dt.getSeconds()).slice(-2);
       //result += ('000' + dt.getMilliseconds()).slice(-3);
       return result;
       }
       }])

   .factory('Wait', [ '$rootScope', function($rootScope) {
   return function(directive) {
       // Display a spinning icon in the center of the screen to freeze the 
       // UI while waiting on async things to complete (i.e. API calls).    
       //   Wait('start' | 'stop');
       if (directive == 'start' && !$rootScope.waiting) {
          $rootScope.waiting = true;
          var docw = $(document).width(); 
          var doch = $(document).height();
          var spinnyw = $('.spinny').width();
          var spinnyh = $('.spinny').height();
          var x = (docw - spinnyw) / 2; 
          var y = (doch - spinnyh) / 2;
          $('.overlay').css({
              width: $('html').width(),
              height: $(document).height() + 200
              }).fadeIn();
          $('.spinny').css({
              top: y, 
              left: x
              }).fadeIn(400);
       }
       else {
          $rootScope.waiting = false;
          $('.spinny, .overlay').fadeOut(1000);
       }
       }
       }])
   
   .factory('HideElement', [ function() {
   return function(selector, action) {
       // Fade-in a cloack or vail or a specific element
       var target = $(selector);
       var width = target.css('width');
       var height = target.css('height');
       var position = target.position();
       var parent = target.parent();
       var borderRadius = target.css('border-radius');
       var backgroundColor = target.css('background-color');
       var margin = target.css('margin');
       var padding = target.css('padding');
       parent.append("<div id=\"curtain-div\" style=\"" + 
           "position: absolute;" +
           "top: " + position.top + "px; " + 
           "left: " + position.left + "px; " + 
           "z-index: 1000; " +
           "width: " + width + "; " + 
           "height: " + height + "; " + 
           "background-color: " + backgroundColor + "; " +
           "margin: " + margin + "; " + 
           "padding: " + padding + "; " +
           "border-radius: " + borderRadius + "; " + 
           "opacity: .75; " + 
           "display: none; " +
           "\"></div>");
       $('#curtain-div').show(0, action);
       }
       }])

   .factory('ShowElement', [ function() {
   return function() {
       // And Fade-out the cloack revealing the element
       $('#curtain-div').fadeOut(500, function() { $(this).remove(); });
       }
       }])

   .factory('GetChoices', [ 'Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
   return function(params) {
       // Get dropdown options

       var scope = params.scope;
       var url = params.url; 
       var field = params.field;
       var emit_callback = params.emit;

       Rest.setUrl(url);
       Rest.options()
           .success( function(data, status, headers, config) {
               scope.$emit(emit_callback, data.actions['GET'][field].choices);
               })
           .error(  function(data, status, headers, config) {
               ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status }); 
               });
       }
       }])

   /* DeugForm(form_name)
    *
    * Use to log the $pristine and $invalid properties of each form element. Helpful when form
    * buttons fail to enable/disable properly. 
    *
    */
   .factory('DebugForm', [ function() {
   return function(form_name) {
       $('form[name="' + form_name + '"]').find('select, input, button, textarea').each(function(index){
           var name = $(this).attr('name');
           if (name) {
              if (scope['job_templates_form'][name]) {
                  console.log(name + ' pristine: ' + scope['job_templates_form'][name].$pristine);
                  console.log(name + ' invalid: ' + scope['job_templates_form'][name].$invalid);
              }
           }
           });
      }
      }]);



