/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * ListGenerator 
 * Pass in a list definition from ListDefinitions and out pops an html template.
 * Use inject method to generate the html and inject into the current view.
 *
 */

angular.module('ListGenerator', ['GeneratorHelpers',])
    .factory('GenerateList', [ '$location', '$compile', '$rootScope', 'SearchWidget', 'PaginateWidget', 
    function($location, $compile, $rootScope, SearchWidget, PaginateWidget) {
    return {
    
    setList: function(list) {
       this.list = list;
       },
 
    attr: function(obj, key) { 
       var result;
       switch (key) {
           case 'ngClick':
                result = "ng-click=\"" + obj[key] + "\" ";
                break;
           case 'ngClass':
                result = "ng-class=\"" + obj[key] + "\" ";
                break;
           case 'ngDisabled':
                result = "ng-disabled=\"" + obj[key] + "\" ";
                break;
           case 'ngBind':
                result = "ng-bind=\"" + obj[key] + "\" ";
                break;
           case 'ngShow':
                result = "ng-show=\"" + obj[key] + "\" ";
                break;
           case 'awToolTip':
                result = "aw-tool-tip=\"" + obj[key] + "\" ";
                break;
           default:
                result = key + "=\"" + obj[key] + "\" ";
       }
       return  result; 
       },

    icon: function(icon) {
       return "<i class=\"" + icon + "\"></i> ";
       },

    has: function(key) {
       return (this.form[key] && this.form[key] != null && this.form[key] != undefined) ? true : false;
       },

    hide: function() {
          $('#lookup-modal').modal('hide');
       },
 
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
       if (options.mode == 'lookup') {
          var element = angular.element(document.getElementById('lookup-modal-body'));  
       }
       else {
          var element = angular.element(document.getElementById('htmlTemplate'));  
       }
       this.setList(list);
       element.html(this.build(options));    // Inject the html
       this.scope = element.scope();         // Set scope specific to the element we're compiling, avoids circular reference
                                             // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       if (options.mode == 'lookup') {
          // options should include {hdr: <dialog header>, action: <function...> }
          this.scope.lookupHeader = options.hdr;
          $('#lookup-modal').modal();
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

       if (options.mode != 'lookup') {
           //Breadcrumbs
           html += "<div class=\"nav-path\">\n";
           html += "<ul class=\"breadcrumb\">\n";
           html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title | capitalize }}</a> " +
                   "<span class=\"divider\">/</span></li>\n";
           html += "<li class=\"active\">";
           if (options.mode == 'select') {
              html += list.selectTitle; 
           }
           else {
              html += list.editTitle;
           }
           html += "</li>\n</ul>\n</div>\n";
       }
      
       //select instructions
       if (options.mode == 'select' && list.selectInstructions) {
          html += "<div class=\"alert alert-info alert-block\">\n";
          html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
          html += "<strong>Hint: </strong>" + list.selectInstructions + "\n";
          html += "</div>\n"
       }
       else if (options.mode == 'edit' && list.editInstructions) {
          html += "<div class=\"alert alert-info alert-block\">\n";
          html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
          html += "<strong>Hint: </strong>" + list.editInstructions + "\n"; 
          html += "</div>\n";
       }

       if (options.mode != 'lookup') {
          html += "<div class=\"well\">\n";
       }
    
       if (options.mode == 'lookup') {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true });
       }
       else {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: false });
       }

       if (options.mode != 'lookup') {
          //actions
          base = $location.path().replace(/^\//,'').split('/')[0];
          html += "<div class=\"list-actions\">\n";
          for (action in list.actions) {
              if (list.actions[action].mode == 'all' || list.actions[action].mode == options.mode) {
                 if ( (list.actions[action].basePaths == undefined) || 
                      (list.actions[action].basePaths && list.actions[action].basePaths.indexOf(base) > -1) ) {
                    html += "<button " + this.attr(list.actions[action], 'ngClick') + 
                            "class=\"btn btn-small " + list.actions[action].class + "\" ";
                    html += (list.actions[action].awToolTip) ? this.attr(list.actions[action],'awToolTip') : "";
                    html += (list.actions[action].awToolTip) ? "data-placement=\"top\" " : "";
                    html += " >" + this.icon(list.actions[action].icon) + "</button> ";
                 }
              }
          }
          if (options.mode == 'select') {
             html += " <button class=\"btn btn-small btn-success\" aw-tool-tip=\"Complete your selection\" " +
                 "ng-click=\"finishSelection()\"><i class=\"icon-ok\"></i> Finished</button>\n";
          }
          html += "</div>\n";
       }

       // table header row
       html += "<table class=\"table table-condensed"
       html += (list.class) ? " " + list.class : "";
       html += (options.mode == 'lookup' || list.hover) ? " table-hover" : ""; 
       html += "\">\n";
       html += "<thead>\n";
       html += "<tr>\n";
       if (list.index) {
          html += "<th>#</th>\n";
       }
       for (var fld in list.fields) {
           html += "<th>" + list.fields[fld].label + "</th>\n";
       }
       if (options.mode == 'select') {
          html += "<th>Select</th>";
       }
       else if (options.mode == 'edit') {
          html += "<th></th>\n";
       }
       html += "</tr>\n";
       html += "</thead>\n";

       // table body
       html += "<tbody>\n";     
       html += "<tr ";
       html += (options.mode == 'lookup' || options.mode == 'select') ? "ng-class=\"" + list.iterator + "_\{\{ " + list.iterator + ".id \}\}_class\" " : "";
       html += "class=\"" + list.iterator + "_class\" ng-repeat=\"" + list.iterator + " in " + list.name + "\"";
       html += (options.mode == 'lookup' || options.mode == 'select') ? " ng-click=\"toggle_" + list.iterator +"({{ " + list.iterator + ".id }})\"" : "";
       html += ">\n";
       if (list.index) {
          html += "<td class=\"index-column\">{{ $index + (" + list.iterator + "Page * " + list.iterator + "PageSize) + 1 }}.</td>\n";
       }
       var cnt = 2;
       var base = (list.base) ? list.base : list.name;
       base = base.replace(/^\//,'');
       for (fld in list.fields) {
           cnt++;  
           html += "<td ";
           html += "<td class=\"" + fld + "-column"; 
           html += (list.fields[fld].class) ? " " + list.fields[fld].class : "";
           html +=  "\" ";  
           html += (list.fields[fld].ngClass) ? this.attr(list.fields[fld], 'ngClass') : "";
           html += ">\n";
           if ((list.fields[fld].key || list.fields[fld].link || list.fields[fld].linkTo || list.fields[fld].ngClick )
                && options.mode != 'lookup' && options.mode != 'select') {
              if (list.fields[fld].linkTo) {
                 html += "<a href=\"#" + list.fields[fld].linkTo + "\">";
              }
              else if (list.fields[fld].ngClick) {
                 html += "<a href=\"\"" + this.attr(list.fields[fld], 'ngClick') + "\">";
              }
              else {
                 html += "<a href=\"#/" + base + "/{{" + list.iterator + ".id }}\">";
              }
           }
           html += (list.fields[fld].icon) ? this.icon(list.fields[fld].icon) : "";
           if (list.fields[fld].ngBind) {       
              html += "{{ " + list.fields[fld].ngBind + " }}";
           }
           else {
              html += "{{" + list.iterator + "." + fld + "}}";    
           }
           html += ((list.fields[fld].key || list.fields[fld].link) && options.mode != 'lookup' && options.mode != 'select') ? "</a>" : "";
           html += "</td>\n";
       }

       if (options.mode == 'select' ) {
          html += "<td><input type=\"checkbox\" name=\"check_{{" + list.iterator + ".id}}\" id=\"check_{{" + list.iterator + ".id}}\" /></td>";
          //ng-click=\"toggle_" + list.iterator +
          //        "({{ " + list.iterator + ".id }}, true)\" 
       }
       else if (options.mode == 'edit') {
          // Row level actions
          html += "<td class=\"actions\">";
          for (action in list.fieldActions) {
              html += "<button class=\"btn"; 
              if (list.fieldActions[action].class) {
                 html += " " + list.fieldActions[action].class;
              }
              html += "\" " + this.attr(list.fieldActions[action],'ngClick');
              html += (list.fieldActions[action].ngShow) ? this.attr(list.fieldActions[action],'ngShow') : "";
              html += (list.fieldActions[action].awToolTip) ? this.attr(list.fieldActions[action],'awToolTip') : "";
              html += (list.fieldActions[action].ngDisabled) ? this.attr(list.fieldActions[action],'ngDisabled') : ""
              html +=">";
              html += (list.fieldActions[action].icon) ? this.icon(list.fieldActions[action].icon) : "";
              html += (list.fieldActions[action].label) ? " " + list.fieldActions[action].label : "";
              html +="</button> ";
          }
          html += "</td>";
       }
       html += "</tr>\n";
            
       // Message for when a collection is empty
       html += "<tr class=\"info\" ng-show=\"" + list.name + " == null || " + list.name + ".length == 0\">\n";
       html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No " + list.iterator + " records matched your search.</div></td>\n";
       html += "</tr>\n";

       // End List
       html += "</tbody>\n";
       html += "</table>\n";  
       
       if (options.mode != 'lookup') {
          html += "</div>\n";    //well
       }

       if (options.mode == 'lookup') {
          html += PaginateWidget({ set: list.name, iterator: list.iterator, mini: true, mode: 'lookup' });
       }
       else {
          html += PaginateWidget({ set: list.name, iterator: list.iterator, mini: true });  
       }
      
       return html;
       
       }
       
}}]);