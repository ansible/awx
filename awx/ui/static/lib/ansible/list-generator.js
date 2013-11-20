/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * ListGenerator 
 * Pass in a list definition from ListDefinitions and out pops an html template.
 * Use inject method to generate the html and inject into the current view.
 *
 */

angular.module('ListGenerator', ['GeneratorHelpers'])
    .factory('GenerateList', [ '$location', '$compile', '$rootScope', 'SearchWidget', 'PaginateWidget', 'Attr', 'Icon',
        'Column', 'DropDown', 'NavigationLink', 'Button',
    function($location, $compile, $rootScope, SearchWidget, PaginateWidget, Attr, Icon, Column, DropDown, NavigationLink, Button) {
    return {
    
    setList: function(list) {
       this.list = list;
       },
 
    attr: Attr,

    icon: Icon,

    has: function(key) {
       return (this.form[key] && this.form[key] != null && this.form[key] != undefined) ? true : false;
       },

    hide: function() {
       $('#lookup-modal').modal('hide');
       },

    button: Button,
 
    inject: function(list, options) {
       // options.mode = one of edit, select or lookup
       //
       // Modes edit and select will inject the list as html into element #htmlTemplate.
       // 'lookup' mode injects the list html into #lookup-modal-body.
       //
       // For options.mode == 'lookup', include the following:
       //
       //     hdr: <lookup dialog header>
       //
       // Inject into a custom element using options.id: <'.selector'>
       // Control breadcrumb creation with options.breadCrumbs: <true | false>
       //
       if (options.mode == 'lookup') {
          var element = angular.element(document.getElementById('lookup-modal-body'));  
       }
       else if (options.id) {
          var element = angular.element(document.getElementById(options.id));  
       }
       else {
          var element = angular.element(document.getElementById('htmlTemplate'));  
       }
       this.setList(list);
       element.html(this.build(options));    // Inject the html
       if (options.prepend) {                // Add any extra HTML passed in options
          element.prepend(options.prepend);
       }
       if (options.append) {
          element.append(options.prepend);
       }

       this.scope = element.scope();         // Set scope specific to the element we're compiling, avoids circular reference
                                             // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       // Reset the scope to prevent displaying old data from our last visit to this list 
       this.scope[list.name] = null;
       this.scope[list.iterator] = null;

       // Remove any lingering tooltip and popover <div> elements
       $('.tooltip').each( function(index) {
           $(this).remove();
           });
       
       $('.popover').each(function(index) {
              // remove lingering popover <div>. Seems to be a bug in TB3 RC1
              $(this).remove();
              });
       $(window).unbind('resize');
       
       try {
           $('#help-modal').empty().dialog('destroy');
       }
       catch(e) {
           //ignore any errors should the dialog not be initialized 
       }

       if (options.mode == 'lookup') {
          // options should include {hdr: <dialog header>, action: <function...> }
          this.scope.formModalActionDisabled = false;
          this.scope.lookupHeader = options.hdr;
          $('#lookup-modal').modal({ backdrop: 'static', keyboard: true });
          $('#lookup-modal').unbind('hidden.bs.modal');
          $(document).bind('keydown', function(e) {
              if (e.keyCode === 27) {
                 $('#lookup-modal').modal('hide');
              }
              });
       }
       
       return this.scope;
       },

    build: function(options) {
       //
       // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML 
       // string to be injected into the current view. 
       //
       var html = '';
       var list = this.list; 

       if (options.activityStream) {
          // Breadcrumbs for activity stream widget
          // Make the links clickable using ng-click function so we can first remove the stream widget
          // before navigation
          html += "<div class=\"nav-path\">\n";
          html += "<ul class=\"breadcrumb\">\n";
          html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"\" ng-click=\"{{ crumb.ngClick }}\">{{ crumb.title | capitalize }}</a></li>\n";
          html += "<li class=\"active\">";
          html += list.editTitle;
          html += "</li>\n</ul>\n</div>\n";
       }
       else if (options.mode != 'lookup' && (options.breadCrumbs == undefined || options.breadCrumbs == true)) {
           //Breadcrumbs
           html += "<div class=\"nav-path\">\n";
           html += "<ul class=\"breadcrumb\">\n";
           html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title | capitalize }}</a></li>\n";
           
           if (list.navigationLinks) {
              var navigation = list.navigationLinks;
              if (navigation['ngHide']) {
                  html += "<li class=\"active\" ng-show=\"" + navigation['ngHide'] + "\">";
                  html += list.editTitle;
                  html += "</li>\n";
                  html += "<li class=\"active\" ng-hide=\"" + navigation['ngHide'] + "\"> </li>\n";
              }
              else {
                  html += "<li class=\"active\"> </li>\n";
                  html += "</ul>\n";
              }
              html += "<div class=\"dropdown\" ";
              html += (navigation['ngHide']) ? Attr(navigation, 'ngHide') : '';
              html += ">\n";
              for (var itm in navigation) {
                  if (typeof navigation[itm] == 'object' && navigation[itm].active) {
                     html += "<a href=\"\" class=\"toggle\" ";
                     html += "data-toggle=\"dropdown\" ";
                     html += ">" + navigation[itm].label + " <i class=\"icon-chevron-sign-down crumb-icon\"></i></a>";
                     break;
                  }
              }
              html += "<ul class=\"dropdown-menu\" role=\"menu\">\n";
              for (var itm in navigation) {
                  if (typeof navigation[itm] == 'object') {
                     html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"" +
                         navigation[itm].href + "\" ";
                     // html += (navigation[itm].active) ? "class=\"active\" " : "";
                     html += ">";
                     html += "<i class=\"icon-ok\" style=\"visibility: ";
                     html += (navigation[itm].active) ? "visible" : "hidden";
                     html += "\"></i> ";
                     html += navigation[itm].label;
                     html += "</a></li>\n";
                  }
              }
              html += "</ul>\n";
              html += "</div><!-- dropdown -->\n";
              html += "</div><!-- nav-path -->\n";
           }
           else {
              html += "<li class=\"active\">";
              if (options.mode == 'select') {
                 html += list.selectTitle; 
              }
              else {
                 html += list.editTitle;
              }
              html += "</li>\n</ul>\n</div>\n";
           }
       }
       
       if (options.mode == 'edit' && list.editInstructions) {
          html += "<div class=\"alert alert-info alert-block\">\n";
          html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
          html += "<strong>Hint: </strong>" + list.editInstructions + "\n"; 
          html += "</div>\n";
       }
       
       if (options.mode != 'lookup' && (list.well == undefined || list.well == true)) {
          html += "<div class=\"well\">\n";
       }
       
       /*
       if (list.editTitle.match(/^Inventory Summary/)) {
          html += "<div class=\"row groups-issue\">\n";
          html += "<div class=\"col-lg-12\">\n";
          html += "<label class=\"checkbox-inline pull-right\"><input type=\"checkbox\" ng-model=\"groupFailureFilter\" " +
              "ng-change=\"search()\" id=\"groups-issue-chbox\"> Show only groups with errors</label>\n";
          html += "</div>\n";
          html += "</div>\n";
       }   
       */
       
       if (options.searchSize) {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true , size: options.searchSize, 
              searchWidgets: list.searchWidgets });
       } 
       else if (options.mode == 'summary') {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true , size: 'col-lg-6' });
       }
       else if (options.mode == 'lookup' || options.id != undefined) {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true , size: 'col-lg-8' });
       }
       else {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true });
       }
     
       if (options.mode != 'lookup') {
          //actions
          var base = $location.path().replace(/^\//,'').split('/')[0];
          
          html += "<div class=\"";
          if (options.searchSize) {
             // User supplied searchSize, calc the remaining
             var size = parseInt(options.searchSize.replace(/([A-Z]|[a-z]|\-)/g,''));
             size = (list.searchWidgets) ? list.searchWidgets * size : size;
             html += 'col-lg-' + (12 - size);
          }
          else if (options.mode == 'summary') {
             html += 'col-lg-6';
          }
          else if (options.id != undefined) {
             html += "col-lg-4"; 
          }
          else { 
             html += "col-lg-8 col-md-6";
          }
          html += "\">\n";
          
          html += "<div class=\"list-actions\">\n";
          // all but refresh button
          for (action in list.actions) {
              if (list.actions[action].mode == 'all' || list.actions[action].mode == options.mode) {
                 if ( (list.actions[action].basePaths == undefined) || 
                      (list.actions[action].basePaths && list.actions[action].basePaths.indexOf(base) > -1) ) {
                    html += this.button(list.actions[action], action);
                 }
              }
          }

          //select instructions
          if (options.mode == 'select' && list.selectInstructions) {
             var btn = {
                 awPopOver: list.selectInstructions,
                 dataPlacement: 'left',
                 dataContainer: 'body',
                 icon: "icon-question-sign",
                 'class': 'btn-xs btn-help btn-info',
                 awToolTip: 'Click for help',
                 dataTitle: 'Help',
                 iconSize: 'large'
                 };
             html += this.button(btn, 'select');
          }

          html += "</div><!-- list-acitons -->\n";
          html += "</div><!-- col-lg-7 -->\n";
       }
       else {
          html += "<div class=\"col-lg-7\"></div>\n";
       }

       html += "</div><!-- row -->\n";
       
       // Add a title and optionally a close button (used on Inventory->Groups)
       if (options.mode !== 'lookup' && list.showTitle) {
          html += "<div class=\"form-title\">";
          html += (options.mode == 'edit' || options.mode == 'summary') ? list.editTitle : list.addTitle;
          html += "</div>\n";
       }

       // table header row
       html += "<table id=\"" + list.name + "_table\" ";
       html += "class=\"table"
       html += (list['class']) ? " " + list['class'] : "";
       html += (options.mode !== 'summary' && (options.mode == 'lookup' || options.id)) ? ' table-hover-inverse' : '';
       html += (list.hover) ? ' table-hover' : '';
       html += (options.mode == 'summary') ? ' table-summary' : '';
       html += "\" ";
       html += ">\n";
       html += "<thead>\n";
       html += "<tr>\n";
       if (list.index) {
          html += "<th>#</th>\n";
       }
       for (var fld in list.fields) {
           if ( (list.fields[fld].searchOnly == undefined || list.fields[fld].searchOnly == false) &&
                !(options.mode == 'lookup' && list.fields[fld].excludeModal !== undefined && list.fields[fld].excludeModal == true) ) {
              html += "<th class=\"list-header";
              html += (list.fields[fld].columnClass) ? " " + list.fields[fld].columnClass : "";
              html += "\" id=\""; 
              html += (list.fields[fld].id) ? list.fields[fld].id : fld + "-header";
              html += "\"";
              html += (list.fields[fld].columnShow) ? " ng-show=\"" + list.fields[fld].columnShow + "\" " : "";
              html += (list.fields[fld].nosort === undefined || list.fields[fld].nosort !== true) ? "ng-click=\"sort('" + fld + "')\"" : "";
              html += ">";
              html += list.fields[fld].label; 
              if (list.fields[fld].nosort === undefined || list.fields[fld].nosort !== true) {
                 html += " <i class=\"";
                 if (list.fields[fld].key) {
                    if (list.fields[fld].desc) {
                       html += "icon-sort-down";
                    }
                    else {
                       html += "icon-sort-up";
                    }
                 }
                 else {
                    html += "icon-sort";
                 }
                 html += "\"></i></a>";
              }
              html += "</th>\n";
           }
       }
       if (options.mode == 'select' || options.mode == 'lookup') {
          html += "<th>Select</th>";
       }
       else if (options.mode == 'edit') {
          html += "<th class=\"actions-column\"></th>\n";
       }
       html += "</tr>\n";
       html += "</thead>\n";

       // table body
       html += "<tbody>\n";     
       html += "<tr ";
       html += (options.mode == 'lookup' || options.mode == 'select') ? "ng-class=\"" + list.iterator + ".success_class\" " : "";
       html += "class=\"" + list.iterator + "_class\" ng-repeat=\"" + list.iterator + " in " + list.name; 
       html += (list.orderBy) ? " | orderBy:'" + list.orderBy + "'" : "";
       html += (list.filterBy) ? " | filter: " + list.filterBy : ""; 
       html += "\"";
       html += ">\n";
       if (list.index) {
          html += "<td class=\"index-column\">{{ $index + (" + list.iterator + "Page * " + list.iterator + "PageSize) + 1 }}.</td>\n";
       }
       var cnt = 2;
       var base = (list.base) ? list.base : list.name;
       base = base.replace(/^\//,'');
       for (fld in list.fields) {
           cnt++;  
           if ( (list.fields[fld].searchOnly == undefined || list.fields[fld].searchOnly == false) &&
                !(options.mode == 'lookup' && list.fields[fld].excludeModal !== undefined && list.fields[fld].excludeModal == true) ) {
              html += Column({ list: list, fld: fld, options: options, base: base });
           }
       }

       if (options.mode == 'select' || options.mode == 'lookup') {
          html += "<td><input type=\"checkbox\" ng-model=\"" + list.iterator + ".checked\" name=\"check_{{" + 
              list.iterator + ".id }}\" ng-click=\"toggle_" + list.iterator +"({{ " + list.iterator + ".id }}, true)\" ng-true-value=\"1\" " +
              "ng-false-value=\"0\" id=\"check_{{" + list.iterator + ".id}}\" /></td>";
       }
       else if (options.mode == 'edit' || options.mode == 'summary') {
          // Row level actions
          html += "<td class=\"actions\">";
          for (action in list.fieldActions) {
              if (list.fieldActions[action].type && list.fieldActions[action].type == 'DropDown') {
                 html += DropDown({ 
                     list: list,
                     fld: action, 
                     options: options, 
                     base: base, 
                     type: 'fieldActions',
                     td: false
                     });
              }
              else {
                 html += this.button(list.fieldActions[action]);
              }
          }
          html += "</td>";
       }
       html += "</tr>\n";
            
       // Message for when a collection is empty
       html += "<tr class=\"info\" ng-show=\"" + list.iterator + "Loading == false && (" + list.name + " == null || " + list.name + ".length == 0)\">\n";
       html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No records matched your search.</div></td>\n";
       html += "</tr>\n";
       
       // Message for loading
       html += "<tr class=\"info\" ng-show=\"" + list.iterator + "Loading == true\">\n";
       html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">Loading...</div></td>\n";
       html += "</tr>\n";

       // End List
       html += "</tbody>\n";
       html += "</table>\n";
       
       if (options.mode == 'select' && (options.selectButton == undefined || options.selectButton == true)) {
          html += "<div class=\"navigation-buttons\">\n";
          html += " <button class=\"btn btn-sm btn-primary pull-right\" aw-tool-tip=\"Complete your selection\" " +
              "ng-click=\"finishSelection()\" ng-disabled=\"selected.length == 0\"><i class=\"icon-check\"></i> Select</button>\n";
          html += "</div>\n";
       }
       
       if (options.mode != 'lookup' && (list.well == undefined || list.well == true)) {
          html += "</div>\n";    //well
       }

       if ( options.mode == 'lookup' || (options.id && options.id == "form-modal-body") ) {
          html += PaginateWidget({ set: list.name, iterator: list.iterator, mini: true, mode: 'lookup' });
       }
       else {
          html += PaginateWidget({ set: list.name, iterator: list.iterator, mini: true });
       }
       
       return html;
       
       }
       
}}]);