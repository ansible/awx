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
        'Column', 
    function($location, $compile, $rootScope, SearchWidget, PaginateWidget, Attr, Icon, Column) {
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
       this.scope = element.scope();         // Set scope specific to the element we're compiling, avoids circular reference
                                             // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       if (options.mode == 'lookup') {
          // options should include {hdr: <dialog header>, action: <function...> }
          this.scope.lookupHeader = options.hdr;
          $('.popover').remove();  //remove any lingering pop-overs
          $('#lookup-modal').modal({ backdrop: 'static', keyboard: false });
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

       if (options.mode != 'lookup' && (options.breadCrumbs == undefined || options.breadCrumbs == true)) {
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

       if (options.mode != 'lookup' && (list.well == undefined || list.well == 'true')) {
          html += "<div class=\"well\">\n";
       }
    
       if (options.mode == 'lookup' || options.id != undefined) {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: true });
       }
       else {
          html += SearchWidget({ iterator: list.iterator, template: list, mini: false });
       }

       if (options.mode != 'lookup') {
          //actions
          var base = $location.path().replace(/^\//,'').split('/')[0];
          html += "<div class=\"list-actions\">\n";
          for (action in list.actions) {
              if (list.actions[action].mode == 'all' || list.actions[action].mode == options.mode) {
                 if ( (list.actions[action].basePaths == undefined) || 
                      (list.actions[action].basePaths && list.actions[action].basePaths.indexOf(base) > -1) ) {
                    html += "<button " + this.attr(list.actions[action], 'ngClick') + "class=\"btn";
                    html += (list.actions[action]['class']) ?  " " + list.actions[action]['class'] : " btn-small";
                    html += "\" ";
                    html += (list.actions[action].ngHide) ? this.attr(list.actions[action],'ngHide') : "";
                    html += (list.actions[action].awToolTip) ? this.attr(list.actions[action],'awToolTip') : "";
                    html += (list.actions[action].awToolTip && list.actions[action].dataPlacement == undefined) ? "data-placement=\"top\" " : "";
                    html += (list.actions[action].awPopOver) ? "aw-pop-over=\"" + 
                        list.actions[action].awPopOver.replace(/[\'\"]/g, '&quot;') + "\" " : "";
                    html += (list.actions[action].dataPlacement) ? this.attr(list.actions[action], 'dataPlacement') : "";
                    html += (list.actions[action].dataContainer) ? this.attr(list.actions[action], 'dataContainer') : "";
                    html += (list.actions[action].dataTitle) ? this.attr(list.actions[action], 'dataTitle') : "";
                    html += " >" + this.attr(list.actions[action],'icon');
                    html += (list.actions[action].label) ? " " + list.actions[action].label : ""; 
                    html += "</button> ";
                 }
              }
          }
          if (options.mode == 'select' && (options.selectButton == undefined || options.selectButton == true)) {
             html += " <button class=\"btn btn-small btn-success\" aw-tool-tip=\"Complete your selection\" " +
                 "ng-click=\"finishSelection()\"><i class=\"icon-ok\"></i> Finished</button>\n";
          }
          html += "</div>\n";
       }

       // table header row
       html += "<table class=\"table table-condensed"
       html += (list['class']) ? " " + list['class'] : "";

       // Add the correct hover class
       if (options.id) {
          html += " table-hover-inverse";
       }
       else if (options.mode == 'lookup' || list.hover) {
          html += " table-hover";
       }

       html += "\">\n";
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
       html += "class=\"" + list.iterator + "_class\" ng-repeat=\"" + list.iterator + " in " + list.name; 
       html += (list.orderBy) ? " | orderBy:'" + list.orderBy + "'" : "";
       html += (list.filterBy) ? " | filter: " + list.filterBy : ""; 
       html += "\"";
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
           if ( (list.fields[fld].searchOnly == undefined || list.fields[fld].searchOnly == false) &&
                !(options.mode == 'lookup' && list.fields[fld].excludeModal !== undefined && list.fields[fld].excludeModal == true) ) {
              html += Column({ list: list, fld: fld, options: options, base: base });
           }
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
              html += (list.fieldActions[action]['class']) ? " " + list.fieldActions[action]['class'] : " btn-small";
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
       
       if (options.mode != 'lookup' && (list.well == undefined || list.well == 'true')) {
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