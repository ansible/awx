/************************************
 *
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  Utility functions
 *
 */
angular.module('Utilities',['RestServices', 'Utilities'])
   
   .factory('ClearScope', [ function() {
   return function(id) {
       
       var element = document.getElementById(id);
       if (element) {
           var scope = angular.element(element).scope();
           scope.$destroy();
       }

       $('.tooltip').each( function(index) {
           // Remove any lingering tooltip and popover <div> elements
           $(this).remove();
           });
   
       $('.popover').each(function(index) {
           // remove lingering popover <div>. Seems to be a bug in TB3 RC1
           $(this).remove();
           });

       $(window).unbind('resize');
       
       }
       }])

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

   .factory('ProcessErrors', ['$rootScope', '$cookieStore', '$log', '$location', 'Alert',
   function($rootScope, $cookieStore, $log, $location, Alert) {
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
       else if ( (status == 401 && data.detail && data.detail == 'Token is expired') || 
           (status == 401 && data.detail && data.detail == 'Invalid token') ) {
          $rootScope.sessionTimer.expireSession();
          $location.url('/login');
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
   
   .factory('HelpDialog', ['$rootScope', '$location', function($rootScope, $location) {
   return function(params) {
       // Display a help dialog
       //
       // HelpDialog({ defn: <HelpDefinition> })
       //
       
       function showHelp(params) {
           // Using a function inside a function so we can recurse 
           // over the steps in the help story

           var defn = params.defn;
           var nxtStory = { story: { steps: { } } };
           var width, height;
           
           function buildHtml(step) {
               var html = ''; 
               html += (step.intro) ? "<div class=\"help-intro\">" + step.intro + "</div>" : "";
               if (step.img) {
                  html += "<img src=\"" + $basePath + "img/help/" + step.img.src + "\" ";
                  html += "style=\"";
                  html += (step.img.maxWidth) ? "max-width:" + step.img.maxWidth + "px;" : "";
                  html += (step.img.maxHeight) ? " max-height: " + step.img.maxHeight + "px;" : "";
                  html += "\" ";
                  html += ">";
               }
               html += (step.box) ? "<div class=\"help-box\">" + step.box + "</div>" : "";
               return html;
               }
           
           var nxt;
           for (var step in defn.story.steps) {
               nxt = step;
               break;
           }
           
           width = (defn.story.steps[nxt].width !== undefined) ? defn.story.steps[nxt].width : 500; 
           height = (defn.story.steps[nxt].height !== undefined) ? defn.story.steps[nxt].height : 600;
           
           if (Object.keys(defn.story.steps).length > 1) {
              // We have multiple steps
              for (var step in defn.story.steps) {
                  if (step !== nxt) {
                     nxtStory.story.steps[step] = defn.story.steps[step];
                  }
              }
              nxtStory.story.hdr = defn.story.hdr; 

              nxtStep = function() {
                  showHelp({ defn: nxtStory });
                  }
              
              try {
                  $('#help-modal').dialog('hide');
              }
              catch(e) {
                  // ignore
              }
              $('#help-modal').html(buildHtml(defn.story.steps[nxt])).dialog({
                  position: { my: "center top", at: "center top+150", of: 'body' },
                  title: defn.story.hdr, 
                  width: width,
                  height: height,
                  buttons: [{ text: "Next", click: nxtStep }],
                  closeOnEscape: true,
                  show: 500,
                  hide: 500,
                  close: function() { $('#help-modal').empty(); }
                  });
              $('.ui-dialog-buttonset button').addClass('btn btn-primary').focus();
              $('.ui-dialog-titlebar-close').empty().removeClass('close').removeClass('ui-dialog-titlebar-close').addClass('close').append('x');
           }
           else {
              try {
                  $('#help-modal').dialog('hide');
              }
              catch(e) {
                  // ignore
              }
              $('#help-modal').html(buildHtml(defn.story.steps[nxt])).dialog({
                  position: { my: "center top", at: "center top+150", of: 'body' },
                  title: defn.story.hdr, 
                  width: width,
                  height: height,
                  buttons: [ { text: "OK", click: function() { $( this ).dialog( "close" ); } } ],
                  closeOnEscape: true,
                  show: 500,
                  hide: 500,
                  close: function() { $('#help-modal').empty(); }
                  });
              $('.ui-dialog-buttonset button').addClass('btn btn-primary').focus();
              $('.ui-dialog-titlebar button').empty().removeClass('close').removeClass('ui-dialog-titlebar-close').addClass('close').append('x');
           }
           }
       
       showHelp(params);

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
          var docw = $(window).width(); 
          var doch = $(window).height();
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
       else if (directive == 'stop' && $rootScope.waiting){
          $('.spinny, .overlay').fadeOut(400, function(){ $rootScope.waiting = false; });
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
       var variable = params.variable;
       var callback = params.callback;   // Optional. Provide if you want scop.$emit on completion. 
       var choice_name = params.choice_name;   // Optional. Used when data is in something other than 'choices'
       
       if (scope[variable]) {
          scope[variable].length = 0;
       }
       else {
          scope[variable] = [];
       }
       
       Rest.setUrl(url);
       Rest.options()
           .success( function(data, status, headers, config) {
               var choices = (choice_name) ? data.actions.GET[field][choice_name] : data.actions.GET[field].choices
               // including 'name' property so list can be used by search
               for (var i=0; i < choices.length; i++) {
                   scope[variable].push({ label: choices[i][1], value: choices[i][0], name: choices[i][1]});
               }
               if (callback) {
                  scope.$emit(callback);
               }
               })
           .error(  function(data, status, headers, config) {
               ProcessErrors(scope, data, status, null,
                    { hdr: 'Error!', msg: 'Failed to get ' + url + '. GET status: ' + status }); 
               });
       }
       }])

   /* DeugForm({ form: <form object>, scope: <current scope object> });
    *
    * Use to log the $pristine and $valid properties of each form element. Helpful when form
    * buttons fail to enable/disable properly. 
    *
    */
   .factory('DebugForm', [ function() {
   return function(params) {
       var form = params.form; 
       var scope = params.scope; 
       for (var fld in form.fields) {
          if (scope[form.name + '_form'][fld]) {
             console.log(fld + ' valid: ' + scope[form.name + '_form'][fld].$valid); 
          }
          if (form.fields[fld].sourceModel) {
             if (scope[form.name + '_form'][form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField]) {
                console.log(form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField + ' valid: ' +
                    scope[form.name + '_form'][form.fields[fld].sourceModel + '_' + form.fields[fld].sourceField].$valid);
             }
          }
      }
      console.log('form pristine: ' + scope[form.name + '_form'].$pristine);
      console.log('form valid: ' + scope[form.name + '_form'].$valid);
      }
      }])
   
   /* Empty()
    *
    * Test if a value is 'empty'. Returns true if val is null | '' | undefined.
    * Only works on non-Ojbect types.
    *
    */
   .factory('Empty', [ function() {
   return function(val) {
       return (val === null || val === undefined || val === '') ? true : false;
       }
       }]);



