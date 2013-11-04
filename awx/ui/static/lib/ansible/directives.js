/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * Custom directives for form validation 
 *
 */

var INTEGER_REGEXP = /^\-?\d*$/;


angular.module('AWDirectives', ['RestServices', 'Utilities', 'AuthService', 'HostsHelper'])
    // awpassmatch:  Add to password_confirm field. Will test if value
    //               matches that of 'input[name="password"]'
    .directive('awpassmatch', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                var associated = attrs.awpassmatch;
                var password = $('input[name="' + associated + '"]').val(); 
                if (viewValue == password) {
                   // it is valid
                   ctrl.$setValidity('awpassmatch', true);
                   return viewValue;
                } else {
                   // it is invalid, return undefined (no model update)
                   ctrl.$setValidity('awpassmatch', false);
                   return undefined;
                }
                });
            }
        }
        })
    
    // caplitalize  Add to any input field where the first letter of each
    //              word should be capitalized. Use in place of css test-transform.
    //              For some reason "text-transform: capitalize" in breadcrumbs
    //              causes a break at each blank space. And of course, 
    //              "autocapitalize='word'" only works in iOS. Use this as a fix.
    .directive('capitalize', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                var values = viewValue.split(" ");
                var result = "";
                for (i = 0; i < values.length; i++){
                    result += values[i].charAt(0).toUpperCase() + values[i].substr(1) + ' ';
                }
                result = result.trim();
                if (result != viewValue) {
                   ctrl.$setViewValue(result);
                   ctrl.$render();
                }
                return result;
                });
            }
        }
        })

    // integer  Validate that input is of type integer. Taken from Angular developer
    //          guide, form examples. Add min and max directives, and this will check
    //          entered values is within the range.
    //
    //          Use input type of 'text'. Use of 'number' casuses browser validation to
    //          override/interfere with this directive.
    .directive('integer', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift(function(viewValue) {
                ctrl.$setValidity('min', true);
                ctrl.$setValidity('max', true);
                if (INTEGER_REGEXP.test(viewValue)) {
                   // it is valid
                   ctrl.$setValidity('integer', true);
                   if ( elm.attr('min') &&
                        ( viewValue == '' || viewValue == null || parseInt(viewValue) < parseInt(elm.attr('min')) ) ) {
                      ctrl.$setValidity('min', false);
                      return undefined;  
                   }
                   if ( elm.attr('max') && ( parseInt(viewValue) > parseInt(elm.attr('max')) ) ) {
                      ctrl.$setValidity('max', false);
                      return undefined;  
                   }
                   return viewValue;
                } else {
                  // it is invalid, return undefined (no model update)
                  ctrl.$setValidity('integer', false);
                  return undefined;
                }
                });
            }
        }
        })
  
    //
    // awRequiredWhen: { variable: "<variable to watch for true|false>", init:"true|false" }
    //
    // Make a field required conditionally using a scope variable. If the scope variable is true, the
    // field will be required. Otherwise, the required attribute will be removed. 
    //  
    .directive('awRequiredWhen', function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            
            function checkIt () {
               var viewValue = elm.val();
               var txt, label, p, l, s;
               validity = true;
               if ( scope[attrs.awRequiredWhen] && (elm.attr('required') == null || elm.attr('required') == undefined) ) {
                  $(elm).attr('required','required');
                  if ($(elm).hasClass('lookup')) {
                     $(elm).parent().parent().parent().find('label').first().addClass('prepend-asterisk');
                  }
                  else {
                     $(elm).parent().parent().find('label').first().addClass('prepend-asterisk');
                  }
               }
               else if (!scope[attrs.awRequiredWhen]) {
                  elm.removeAttr('required');
                  if ($(elm).hasClass('lookup')) {
                     label = $(elm).parent().parent().parent().find('label').first();
                     label.removeClass('prepend-asterisk');
                  }
                  else {
                     $(elm).parent().parent().find('label').first().removeClass('prepend-asterisk');
                  }
               }
               if (scope[attrs.awRequiredWhen] && (viewValue == undefined || viewValue == null || viewValue == '')) {
                  validity = false;
               }
               ctrl.$setValidity('required', validity);
               }
            
            if (attrs.awrequiredInit !== undefined && attrs.awrequiredInit !== null) {
               scope[attrs.awRequiredWhen] = attrs.awrequiredInit;
               checkIt();
            }
            
            scope.$watch(attrs.awRequiredWhen, function() {
                // watch for the aw-required-when expression to change value
                checkIt();
                });

            scope.$watch($(elm).attr('name'), function() {
                // watch for the field to change value
                checkIt();
                });
            }
        }
        })

    // lookup   Validate lookup value against API
    //           
    .directive('awlookup', ['Rest', function(Rest) {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                if (viewValue !== '' && viewValue !== null) {
                   var url = elm.attr('data-url');
                   url = url.replace(/\:value/,escape(viewValue));
                   scope[elm.attr('data-source')] = null;
                   Rest.setUrl(url);
                   Rest.get().then( function(data) {
                       var results = data.data.results;
                       if (results.length > 0) {
                          scope[elm.attr('data-source')] = results[0].id;
                          scope[elm.attr('name')] = results[0].name;
                          ctrl.$setValidity('required', true); 
                          ctrl.$setValidity('awlookup', true);
                          return viewValue;
                       }
                       else {
                          ctrl.$setValidity('required', true); 
                          ctrl.$setValidity('awlookup', false);
                          return undefined;
                       }
                       });
                }
                else {
                   ctrl.$setValidity('awlookup', true);
                   scope[elm.attr('data-source')] = null;
                }
                })
            }
        }
        }])
    
    //
    // awValidUrl
    //           
    .directive('awValidUrl', [ function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            ctrl.$parsers.unshift( function(viewValue) {
                var validity = true;
                if (viewValue !== '') {
                   ctrl.$setValidity('required', true);
                   var rgx = /^(https|http|ssh)\:\/\//;
                   var rgx2 = /\@/g;
                   if (!rgx.test(viewValue) || rgx2.test(viewValue)) {
                      validity = false;
                   }
                }
                ctrl.$setValidity('awvalidurl', validity); 
                })
            }
        }
        }])

    /*  
     *  Enable TB tooltips. To add a tooltip to an element, include the following directive in
     *  the element's attributes:
     *
     *     aw-tool-tip="<< tooltip text here >>"
     *
     *  Include the standard TB data-XXX attributes to controll a tooltip's appearance.  We will 
     *  default placement to the left and delay to 2 seconds.
     */ 
    .directive('awToolTip', function() {
       return function(scope, element, attrs) {
           var delay = (attrs.delay != undefined && attrs.delay != null) ? attrs.delay : $AnsibleConfig.tooltip_delay;
           var placement = (attrs.placement != undefined && attrs.placement != null) ? attrs.placement : 'left';
           $(element).on('hidden.bs.tooltip', function( ) {
               // TB3RC1 is leaving behind tooltip <div> elements. This will remove them
               // after a tooltip fades away. If not, they lay overtop of other elements and 
               // honk up the page. 
               $('.tooltip').each(function(index) {
                   $(this).remove();
                   });  
               });
           $(element).tooltip({ placement: placement, delay: delay, html: true, title: attrs.awToolTip, container: 'body' });
       }
       })
     
    /*  
     *  Enable TB pop-overs. To add a pop-over to an element, include the following directive in
     *  the element's attributes:
     *
     *     aw-pop-over="<< pop-over html here >>"
     *
     *  Include the standard TB data-XXX attributes to controll the pop-over's appearance.  We will 
     *  default placement to the left, delay to 0 seconds, content type to HTML, and title to 'Help'.
     */ 
    .directive('awPopOver', function() {
        return function(scope, element, attrs) {
            var placement = (attrs.placement != undefined && attrs.placement != null) ? attrs.placement : 'left';
            var title = (attrs.title != undefined && attrs.title != null) ? attrs.title : 'Help';
            var container = (attrs.container !== undefined) ? attrs.container : false;
            $(element).popover({ placement: placement, delay: 0, title: title, 
                content: attrs.awPopOver, trigger: 'manual', html: true, container: container });
            $(element).click(function() {
                var me = $(this).attr('id');
                var e = $(this);
                $('.help-link, .help-link-white').each( function(index) {
                    if (me != $(this).attr('id')) {
                       $(this).popover('hide');
                    }
                    });
                $('.popover').each(function(index) {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    $(this).remove();
                    });
                $(this).popover('toggle');
                });
            $(document).bind('keydown', function(e) {
                if (e.keyCode === 27) {
                   $(element).popover('hide');
                      $('.popover').each(function(index) {
                      // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                         $(this).remove();
                      });
                }
                });
        }
        })

    //
    // Enable jqueryui slider widget on a numeric input field
    //
    // <input type="number" ng-slider name="myfield" min="0" max="100" />
    //
    .directive('ngSlider', [ function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            var name = elm.attr('name');
            $('#' + name + '-slider').slider({
                value: 0,
                step: 1,
                min: elm.attr('min'),
                max: elm.attr('max'),
                slide: function(e, u) {
                   ctrl.$setViewValue(u.value);
                   ctrl.$setValidity('required',true);
                   ctrl.$setValidity('min', true);
                   ctrl.$setValidity('max', true);
                   ctrl.$dirty = true;
                   ctrl.$render();
                   //scope['job_templates_form'].$dirty = true;
                   if (!scope.$$phase) {
                       scope.$digest();
                   }
                   }
                });

            $('#' + name + '-number').change( function() {
                $('#' + name + '-slider').slider('value', parseInt( $(this).val() ));
                });


            }
        }
        }])

    .directive('awMultiSelect', [ function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            $(elm).multiselect  ({
                buttonClass: 'btn-default, btn-mini',
                buttonWidth: 'auto',
                buttonContainer: '<div class="btn-group" />',
                maxHeight: false,
                buttonText: function(options) {
                   if (options.length == 0) {
                       return 'None selected <b class="caret"></b>';
                   }
                   else if (options.length > 3) {
                       return options.length + ' selected  <b class="caret"></b>';
                   }
                   else {
                       var selected = '';
                       options.each(function() {
                           selected += $(this).text() + ', ';
                           });
                       return selected.substr(0, selected.length -2) + ' <b class="caret"></b>';
                   }
                }
                });
            }
        }
        }])

    //
    // Enable jqueryui spinner widget on a numeric input field
    //
    // <input type="number" ng-spinner name="myfield" min="0" max="100" />
    //
    .directive('ngSpinner', [ function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {
            var name = elm.attr('name');
            var disabled = elm.attr('data-disabled');
            var opts = {
                value: 0,
                step: 1,
                min: elm.attr('min'),
                max: elm.attr('max'),
                numberFormat: "d",
                spin: function(e, u) {
                   ctrl.$setViewValue(u.value);
                   ctrl.$setValidity('required',true);
                   ctrl.$setValidity('min', true);
                   ctrl.$setValidity('max', true);
                   ctrl.$dirty = true;
                   ctrl.$render();
                   scope['job_templates_form'].$dirty = true;
                   if (!scope.$$phase) {
                       scope.$digest();
                   }
                   }
                };
            if (disabled) { 
               opts['disabled'] = true;
            }   
            $(elm).spinner(opts);
            }
        }
        }])

    //
    // chkPass
    //
    // Enables use of lib/ansible/pwdmeter.js to check strengh of passwords.
    // See controllers/Users.js for example.
    //
    .directive('chkPass', [ function() {
        return {
        require: 'ngModel',
        link: function(scope, elm, attrs, ctrl) {    
            $(elm).keyup(function() {
                var validity = true;
                var score = chkPass(elm.val());
                if (elm.val()) {
                   validity = (score > $AnsibleConfig.password_strength) ? true : false;
                }
                ctrl.$setValidity('complexity', validity);
                if (!scope.$$phase) {
                   scope.$digest();
                }
                });
            }
        }
        }])
    
    //
    // awRefresh
    //
    // Creates a timer to call scope.refresh(iterator) ever N seconds, where
    // N is a setting in config.js
    //
    .directive('awRefresh', [ '$rootScope', function($rootScope) {
        return {
        link: function(scope, elm, attrs, ctrl) {
            function msg() {
                var num = '' + scope.refreshCnt;
                while (num.length < 2) {
                   num = '0' + num;
                }
                return 'Refresh in ' + num + ' sec.';
            }
            scope.refreshCnt = $AnsibleConfig.refresh_rate;
            scope.refreshMsg = msg();
            if ($rootScope.timer) {
                clearInterval($rootScope.timer);
            }
            $rootScope.timer = setInterval( function() {
                scope.refreshCnt--;
                if (scope.refreshCnt <= 0) {
                   scope.refresh();
                   scope.refreshCnt = $AnsibleConfig.refresh_rate;
                }
                scope.refreshMsg = msg();
                if (!scope.$$phase) {
                   scope.$digest();
                }
                }, 1000);
            }
        }
        }]);



