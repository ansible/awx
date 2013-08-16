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
               validity = true;
               if ( scope[attrs.awRequiredWhen] && (elm.attr('required') == null || elm.attr('required') == undefined) ) {
                  $(elm).attr('required','required');
               }
               else if (!scope[attrs.awRequiredWhen]) {
                  elm.removeAttr('required'); 
               }
               if (scope[attrs.awRequiredWhen] && (viewValue == undefined || viewValue == null || viewValue == '')) {
                  validity = false;
               }
               ctrl.$setValidity('required', validity);
               }
            
            scope[attrs.awRequiredWhen] = attrs.awrequiredInit;
            checkIt();
            
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
                if (viewValue !== '') {
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
           $(element).tooltip({ placement: placement, delay: delay, title: attrs.awToolTip, container: 'body' });
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
                   $(element).popover('destroy');
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

    .directive('awTree', ['Rest', 'ProcessErrors', 'Authorization', '$compile', '$rootScope',
        function(Rest, ProcessErrors, Authorization, $compile, $rootScope) {
        return {
        //require: 'ngModel',
        
        replace: true,
        
        transclude: true,
        
        scope: {
            treeData: '=awTree'
            },
        
        replace: true,
        
        template:
            "<div class=\"search-tree well\" id=\"search-tree-container\">\n" +
            "<ul>\n" +
            "<li id=\"search-node-1000\" data-state=\"closed\" data-hosts=\"{{ treeData[0].hosts}}\" " +
            "data-hosts=\"{{ treeData[0].hosts }}\" " +
            "data-description=\"{{ treeData[0].description }}\" " + 
            "data-failures=\"{{ treeData[0].failures }}\" " +
            "data-groups=\"{{ treeData[0].groups }}\" " + 
            "data-name=\"{{ treeData[0].name }}\">" + 
            "<a href=\"\" class=\"expand\"><i class=\"icon-caret-right\"></i></a> <a href=\"\" class=\"activate active\">{{ treeData[0].name }}</a></li>\n" +
            "</li>\n"+
            "</ul>\n" +
            "</div>\n",

        link: function(scope, elm , attrs) {

            var idx=1000;

            function refresh(parent) {
                var group, title;
                if (parent.attr('data-group-id')) {
                   group = parent.attr('data-group-id');
                   title = '<h4>' + parent.attr('data-name') + '</h4>';
                   title += (parent.attr('data-description') !== "") ? '<p>' + parent.attr('data-description') + '</p>' : ''; 
                }
                else {
                   group = null;
                   title = '<h4>All Hosts</h4>'
                } 
                scope.$emit('refreshHost', group, title);
                }
            
            function activate(e) {
                /* Set the clicked node as active */
                var elm = angular.element(e.target);  //<a>
                var parent = angular.element(e.target.parentNode); //<li>
                $('.search-tree .active').removeClass('active');
                elm.addClass('active');
                refresh(parent);
                }

            function toggle(e) {
                
                var id, parent, elm, icon;
                
                if (e.target.tagName == 'I') {
                   id = e.target.parentNode.parentNode.attributes.id.value;
                   parent = angular.element(e.target.parentNode.parentNode);  //<li>
                   elm = angular.element(e.target.parentNode);  // <a>
                }
                else {
                   id = e.target.parentNode.attributes.id.value;
                   parent = angular.element(e.target.parentNode);
                   elm = angular.element(e.target);
                }
                
                var sibling = angular.element(parent.children()[1]); // <a>
                var state = parent.attr('data-state');
                var icon = angular.element(elm.children()[0]);

                /* Open/close the node and expand */
                if (scope.childrenLoadedRemove) {
                   scope.childrenLoadedRemove();
                }
                scope.childrenLoadedRemove = scope.$on('childrenLoaded', function() {
                    childlists = parent.find('ul');  //look for children
                    if (childlists && childlists.length > 0) {
                       // bind toggle() to click event of each link in the group we clicked on
                       var links = parent.find('a');
                       for (var i=0; i < links.length; i++) {
                           var link = angular.element(links[i]);
                           if (link.hasClass('expand')) {
                              link.unbind('click', toggle);
                              link.bind('click', toggle);
                           }
                           if (link.hasClass('activate')) {
                              link.unbind('click', activate);
                              link.bind('click', activate);
                           }
                       }
                       toggle(e);
                    }
                    else {
                       icon.removeClass('icon-caret-right').addClass('icon-caret-down');
                       //activate(e);
                    }
                    });
 
                
                if (state == 'closed') {
                   // expand the elment
                   var childlists = parent.find('ul');
                   if (childlists && childlists.length > 0) {
                     // already has childen
                     for (var i=0; i < childlists.length; i++) {
                         var listChild = angular.element(childlists[i]);
                         var listParent = angular.element(listChild.parent());
                         if (listParent.attr('id') == id) {
                            angular.element(childlists[i]).removeClass('hidden');
                         }
                         // all the children should be in a closed state
                         var liList = listChild.find('li');
                         for (var j=0; j < liList.length; j++) {
                             var thisList  = angular.element(liList[j]);
                             var anchor = angular.element(thisList.find('a')[0]);
                             var thisIcon = angular.element(anchor.children()[0]);
                             thisIcon.removeClass('icon-caret-down').addClass('icon-caret-right');
                             thisList.attr('data-state', 'closed'); 
                         }
                     }
                     parent.attr('data-state','open'); 
                     icon.removeClass('icon-caret-right').addClass('icon-caret-down');
                   }
                   else {
                     getChildren(elm, parent, sibling);   
                   }
                }
                else {
                   // close the element
                   parent.attr('data-state','closed'); 
                   var icon = angular.element(elm.children()[0]);
                   icon.removeClass('icon-caret-down').addClass('icon-caret-right');
                   var childlists = parent.find('ul');
                   if (childlists && childlists.length > 0) {
                       // has childen
                       for (var i=0; i < childlists.length; i++) {
                           angular.element(childlists[i]).addClass('hidden');
                      }
                   }
                   /* When the active node's parent is closed, activate the parent*/
                   if ($(parent).find('.active').length > 0) {
                      $(parent).find('.active').removeClass('active');
                      sibling.addClass('active');
                      refresh(parent);
                   }
                }
                }

            function getChildren(elm, parent, sibling) {
                var url = parent.attr('data-groups');
                var html = '';
                var token = Authorization.getToken();
                /* For reasons unknown calling Rest fails. It just dies with no errors
                   or any info */
                $.ajax({
                    url: url, 
                    headers: { 'Authorization': 'Token ' + token },
                    dataType: 'json',
                    success: function(data) {
                        // build html and append to parent of clicked link
                        for (var i=0; i < data.results.length; i++) {
                            idx++;
                            html += "<li ";
                            html += "id=\"search-tree-" + idx +"\" ";
                            html += "date-state=\"closed\" ";
                            html += "data-hosts=\"" + data.results[i].related.all_hosts + "\" ";
                            html += "data-description=\"" + data.results[i].description + "\" ";
                            html += "data-failures=\"" +data.results[i].has_active_failures + "\" ";
                            html += "data-groups=\"" + data.results[i].related.children + "\" ";
                            html += "data-name=\"" + data.results[i].name + "\" ";
                            html += "data-group-id=\"" + data.results[i].id + "\">";
                            html += "<a href=\"\" class=\"expand\"><i class=\"icon-caret-right\"></i></a> ";
                            html += "<a href=\"\" class=\"activate\">" + data.results[i].name + "</a></li>\n";
                        }
                        html = (html !== '') ? "<ul>" + html + "</ul>\n" : "";
                        var compiled = $compile(html)(scope);
                        parent.append(compiled);  //append the new list to the parent <li>
                        scope.$emit('childrenLoaded');
                        },
                    error: function(data, status) {
                        ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to get child groups for ' + elm.attr('name') + 
                           '. GET returned: ' + status });
                        }
                    });
                }

            function initialize() {
                var root = angular.element(document.getElementById('search-node-1000'));
                var toggleElm = angular.element(root.find('a')[0]);
                var activateElm = angular.element(root.find('a')[1])
                toggleElm.bind('click', toggle);
                activateElm.bind('click', activate);
                }
            
            if ($rootScope.hostTabInitRemove) {
               $rootScope.hostTabInitRemove();
            }
            $rootScope.hostTabInitRemove = $rootScope.$on('hostTabInit', function(e) {
               var container = angular.element(document.getElementById('search-tree-container'));
               container.empty();
               var html = "<ul>\n" +
                   "<li id=\"search-node-1000\" data-state=\"closed\" data-hosts=\"{{ treeData[0].hosts}}\" " +
                   "data-hosts=\"{{ treeData[0].hosts }}\" " +
                   "data-description=\"{{ treeData[0].description }}\" " + 
                   "data-failures=\"{{ treeData[0].failures }}\" " +
                   "data-groups=\"{{ treeData[0].groups }}\" " + 
                   "data-name=\"{{ treeData[0].name }}\" " +
                   "><a href=\"\" class=\"expand\"><i class=\"icon-caret-right\"></i></a> <a href=\"\" class=\"activate active\">{{ treeData[0].name }}</a>" +
                   "</li>\n" +
                   "</ul>\n";
               var compiled = $compile(html)(scope);
               container.append(compiled);
               initialize();
               // Expand the root node and show All Hosts
               setTimeout(function() {
                   $('#search-node-1000 .expand').click();
                   $('#search-node-1000 .activate').click();
                   }, 500);  
               });

            }
        }
        }]);





