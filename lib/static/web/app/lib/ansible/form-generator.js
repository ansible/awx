/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * FormGenerator 
 * Pass in a form definition from FormDefinitions and out pops an html template.
 * See js/form-definitions.js for form example. For now produces a Twitter Bootstrap
 * horizontal form. 
 * 
 */

angular.module('FormGenerator', ['GeneratorHelpers'])
    .factory('GenerateForm', [ '$compile', 'SearchWidget', 'PaginateWidget', function($compile, SearchWidget, PaginateWidget) {
    return {
    
    setForm: function(form) {
       this.form = form;
       },
 
    attr: function(obj, key) { 
       var result;
       switch(key) {
           case 'ngClick':
               result = "ng-click=\"" + obj[key] + "\" ";
               break;
           case 'ngChange':
               result = "ng-change=\"" + obj[key] + "\" ";
               break;
           case 'ngShow':
               result = "ng-show=\"" + obj[key] + "\" ";
               break;
           case 'trueValue':
               result = "ng-true-value=\"" + obj[key] + "\" ";
               break;
           case 'falseValue':
               result = "ng-false-value=\"" + obj[key] + "\" ";
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
 
    inject: function(form, options) {
       //
       // Use to inject the form as html into the view.  View MUST have an ng-bind for 'htmlTemplate'.
       // Returns scope of form.
       //
       var element = angular.element(document.getElementById('htmlTemplate'));  
       this.setForm(form);
       element.html(this.build(options));    // Inject the html
       this.scope = element.scope();  // Set scope specific to the element we're compiling, avoids circular reference
                                      // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       if (options.related) {
          this.addListeners();
       }

       if (options.mode == 'add') {
          this.applyDefaults();
       }

       this.mode = options.mode;
       
       return this.scope;
       },

    applyDefaults: function() {
       for (fld in this.form.fields) {
           if (this.form.fields[fld].default) {
              this.scope[fld] = this.form.fields[fld].default;
           }
       }
       },

    reset: function() {
       // The form field values cannot be reset with jQuery. Each field is tied to a model, so to clear the field
       // value, you have clear the model.
       this.scope[this.form.name + '_form'].$setPristine();
       for (var fld in this.form.fields) {
           this.scope[fld] = '';        
           this.scope[fld + '_api_error'] = '';
           this.scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField] = '';
           if ( this.form.fields[fld].type == 'lookup' &&
                this.scope[this.form.name + '_form'][this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField] ) {
              this.scope[this.form.name + '_form'][this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField].$setPristine();
           }
           if (this.scope[this.form.name + '_form'][fld]) {
              this.scope[this.form.name + '_form'][fld].$setPristine();
           }
       }
       if (this.mode == 'add') {
          this.applyDefaults();
       }
       },

    addListeners: function() {
       // Listen for accordion collapse events and toggle the header icon
       $('.collapse')
           .on('show', function() {
               var element = $(this).parent().find('.accordion-heading i');
               element.removeClass('icon-angle-down');
               element.addClass('icon-angle-up');
               })
           .on('hide', function() {
               var element = $(this).parent().find('.accordion-heading i');
               element.removeClass('icon-angle-up');
               element.addClass('icon-angle-down');
               });
       },

    build: function(options) {
       //
       // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML 
       // string to be injected into the current view. 
       //
       var html = '';
       
       //Breadcrumbs
       html += "<div class=\"nav-path\">\n";
       html += "<ul class=\"breadcrumb\">\n";
       html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title | capitalize }}</a> " +
               "<span class=\"divider\">/</span></li>\n";
       html += "<li class=\"active\">";
       if (options.mode == 'edit') {
          html += this.form.editTitle;
       }
       else {
          html += this.form.addTitle; 
       }
       html += "</li>\n</ul>\n</div>\n";
       
       // Start the well
       if ( this.has('well') ) {
          html += "<div class=\"well\">\n";
       }

       html += "<form class=\"form-horizontal\" name=\"" + this.form.name + '_form" id="' + this.form.name + '" novalidate>' + "\n";

       html += "<div ng-show=\"flashMessage != null && flashMessage != undefined\" class=\"alert alert-info\">{{ flashMessage }}</div>\n";

       //fields
       for (var fld in this.form.fields) {
           var field = this.form.fields[fld];

           //Assuming horizontal form for now. This will need to be more flexible later.
           
           //text type fields
           if (field.type == 'text' || field.type == 'password' || field.type == 'email') {
              if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
                 html += "<div class=\"control-group\""
                 html += (field.ngShow) ? this.attr(field,'ngShow') : "";
                 html += ">\n";
                 html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
                 html += "<div class=\"controls\">\n"; 
                 html += "<input ";
                 html += this.attr(field,'type');
                 html += "ng-model=\"" + fld + '" ';
                 html += 'name="' + fld + '" ';
                 html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                 html += (field.id) ? this.attr(field,'id') : "";
                 html += (field.placeholder) ? this.attr(field,'placeholder') : "";
                 html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
                 html += (options.mode == 'add' && field.addRequired) ? "required " : "";
                 html += (field.readonly) ? "readonly " : "";
                 html += (field.awPassMatch) ? "awpassmatch " : "";
                 html += (field.capitalize) ? "capitalize " : "";
                 html += "/><br />\n";
                 // Add error messages
                 if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
                    html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                    this.form.name + '_form.' + fld + ".$error.required\">A value is required!</span>\n";
                 }
                 if (field.type == "email") {
                    html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                    this.form.name + '_form.' + fld + ".$error.email\">A valid email address is required!</span>\n";
                 }
                 if (field.awPassMatch) {
                    html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + 
                            ".$error.awpassmatch\">Must match Password value</span>\n";
                 }
                 html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
                 html += "</div>\n";
                 html += "</div>\n";
              }
           }

           //checkbox
           if (field.type == 'checkbox') {
              if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
                 html += "<div class=\"control-group\" "
                 html += (field.ngShow) ? this.attr(field,'ngShow') : "";
                 html += ">\n";
                 html += "<div class=\"controls\">\n";
                 html += "<label class=\"checkbox\">";
                 html += "<input "; 
                 html += this.attr(field,'type');
                 html += "ng-model=\"" + fld + '" ';
                 html += "name=\"" + fld + '" ';
                 html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                 html += (field.id) ? this.attr(field,'id') : "";
                 html += this.attr(field,'trueValue');
                 html += this.attr(field,'falseValue');
                 html += (field.checked) ? "checked " : "";
                 html += (field.readonly) ? "readonly " : "";
                 html += " /> " + field.label + "\n";
                 html += "</label>\n";
                 html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";

                 html += "</div>\n";
                 html += "</div>\n";
              }
           }

           //lookup type fields
           if (field.type == 'lookup') {
              html += "<div class=\"control-group\""
              html += (field.ngShow) ? this.attr(field,'ngShow') : "";
              html += ">\n";
              html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
              html += "<div class=\"controls\">\n";
              html += "<div class=\"input-prepend\">\n";
              html += "<button class=\"btn\" " + this.attr(field,'ngClick') + "><i class=\"icon-search\"></i></button>\n";
              html += "<input class=\"input-medium\" type=\"text\" ";
              html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField +  "\" ";
              html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
              html += (field.ngChange) ? this.attr(field,'ngChange') : "";
              html += (field.id) ? this.attr(field,'id') : "";
              html += (field.placeholder) ? this.attr(field,'placeholder') : "";
              html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
              html += (options.mode == 'add' && field.addRequired) ? "required " : "";
              html += " readonly />\n";
              html += "</div>\n";
              // Add error messages
              if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
                html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</span>\n";
              }
              html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
              html += "</div>\n";
              html += "</div>\n";
           }
       }

       //buttons
       if (this.has('buttons')) {
          html += "<div class=\"control-group\">\n";
          html += "<div class=\"controls buttons\">\n";
       }
       for (var btn in this.form.buttons) {
           var button = this.form.buttons[btn];
           //button
           html += "<button ";
           if (button.class) {
              html += this.attr(button,'class');
           }
           if (button.ngClick) {
              html += this.attr(button,'ngClick');
           }
           if (button.ngDisabled) {
              if (btn !== 'reset') {
                 html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid\" ";
              }
              else {
                 html += "ng-disabled=\"" + this.form.name + "_form.$pristine\" ";   
              }
           }
           html += ">";
           if (button.icon) {
              html += this.icon(button.icon);
           }
           html += button.label + "</button>\n";
       }
       if (this.has('buttons')) {
          html += "</div>\n";
          html += "</div>\n";
       }

       html += "</form>\n";

       if ( this.has('well') ) {
          html += "</div>\n";
       }
       
       if (options.related && this.form.related) {
          html += this.buildCollections();
       }

       return html;
       
       },

    buildCollections: function() {
       //
       // Create TB accordians with imbedded lists for related collections
       // Should not be called directly. Called internally by build().
       //
       var idx = 1;
       var form = this.form;
       var html = "<div class=\"accordion\" id=\"accordion\">\n";
       for (var itm in form.related) {
           if (form.related[itm].type == 'collection') {
              // Start the accordion group
              html += "<div class=\"accordion-group\">\n";
              html += "<div class=\"accordion-heading\">\n";
              html += "<a class=\"accordion-toggle\" data-toggle=\"collapse\" data-parent=\"#accordion\" href=\"#collapse" + idx + "\">";
              html += "<i class=\"icon-angle-down icon-white\"></i>" + form.related[itm].title + "</a>\n";
              html += "</div>\n";
              html += "<div id=\"collapse" + idx + "\" class=\"accordion-body collapse";
              if (form.related[itm].open) {
                 html += " in";   //open accordion on load
              }
              html += "\">\n";
              html += "<div class=\"accordion-inner\">\n";
              html += "<div class=\"well\">\n";

              html += SearchWidget({ iterator: form.related[itm].iterator, template: form.related[itm], mini: true });

              // Add actions(s)
              html += "<div class=\"text-right actions\">\n";
              for (var action in form.related[itm].actions) {
                  html += "<button class=\"btn btn-mini btn-success\" ";
                  html += this.attr(form.related[itm]['actions'][action],'ngClick');
                  html += "><i class=\"" + form.related[itm]['actions'][action].icon + "\"></i></button>\n";
              }
              html += "</div>\n";
              
              // Start the list
              html += "<div class=\"list\">\n";
              html += "<table class=\"table table-condensed\">\n";
              html += "<thead>\n";
              html += "<tr>\n";
              html += "<th>#</th>\n";
              for (var fld in form.related[itm].fields) {
                  html += "<th>" + form.related[itm]['fields'][fld].label + "</th>\n";
              }
              html += "<th></th>\n";
              html += "</tr>\n";
              html += "</thead>";
              html += "<tbody>\n";
              
              html += "<tr ng-repeat=\"" + form.related[itm].iterator + " in " + itm + "\" >\n";
              html += "<td>{{ $index + (" + form.related[itm].iterator + "Page * " + 
                      form.related[itm].iterator + "PageSize) + 1 }}.</td>\n";
              var cnt = 1;
              for (var fld in form.related[itm].fields) {
                  cnt++;
                  html += "<td>{{ " + form.related[itm].iterator + "." + fld + " }}</td>\n";
              }
              
              // Row level actions
              html += "<td class=\"actions\">";
              for (action in form.related[itm].fieldActions) {
                  html += "<button class=\"btn btn-mini"; 
                  if (form.related[itm]['fieldActions'][action].class) {
                     html += " " + form.related[itm]['fieldActions'][action].class;
                  }
                  html += "\" " + this.attr(form.related[itm]['fieldActions'][action],'ngClick') +
                          ">" + this.icon(form.related[itm]['fieldActions'][action].icon) + "</button> ";
              }
              html += "</td>";
              html += "</tr>\n";
              
              // Message for when a related collection is empty
              html += "<tr class=\"info\" ng-show=\"" + itm + " == null || " + itm + ".length == 0\">\n";
              html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No records matched your search.</div></td>\n";
              html += "</tr>\n";

              // End List
              html += "</tbody>\n";
              html += "</table>\n";
              html += "</div>\n";    // close well
              html += "</div>\n";    // close list div

              html += PaginateWidget({ set: itm, iterator: form.related[itm].iterator, mini: true });      
              
              // End Accordion Group
              html += "</div>\n";    // accordion inner
              html += "</div>\n";    // accordion body
              html += "</div>\n";    // accordion group

              idx++;
           }
       }
       html += "</div>\n";

       return html; 
       }
       
}}]);