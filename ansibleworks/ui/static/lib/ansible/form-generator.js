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
           case 'ngOptions':
               result = "ng-options=\"" + obj[key] + "\" ";
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
 
    inject: function(form, options) {
       //
       // Use to inject the form as html into the view.  View MUST have an ng-bind for 'htmlTemplate'.
       // Returns scope of form.
       //
       var element;
       if (options.modal) {
          element = angular.element(document.getElementById('form-modal-body'));
       }
       else {
          var element = angular.element(document.getElementById('htmlTemplate'));
       }

       this.setForm(form);
       element.html(this.build(options));  // Inject the html
       this.scope = element.scope();       // Set scope specific to the element we're compiling, avoids circular reference
                                           // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       if ((!options.modal) && options.related) {
          this.addListeners();
       }

       if (options.mode == 'add') {
          this.applyDefaults();
       }

       if (options.modal) {
          (options.mode == 'add') ? scope.formHeader = form.addTitle : form.editTitle;
          $('#form-modal').modal();
       }

       this.mode = options.mode;
       this.modal = (options.modal) ? true : false;
       
       return this.scope;
       },

    applyDefaults: function() {
       for (fld in this.form.fields) {
           if (this.form.fields[fld].default || this.form.fields[fld].default == 0) {
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
           if (this.form.fields[fld].awPassMatch) {
              this.scope[this.form.name + '_form'][fld].$setValidity('awpassmatch', true); 
           }
           if (this.form.fields[fld].ask) {
              this.scope[fld + '_ask'] = false;
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

    headerField: function(fld, field, options) {
       var html = '';
       if (field.label) {
          html += "<label>" + field.label + "</label>\n";
       }
       html += "<input type=\"text\" name=\"" + fld + "\" ";
       html += "ng-model=\"" + fld + "\" ";
       html += (field.class) ? this.attr(field, "class") : "";
       html += " readonly />\n";
       return html;
       },

    buildField: function(fld, field, options) {
           
       var html='';

       //Assuming horizontal form for now. This will need to be more flexible later.

       //text fields
       if (field.type == 'text' || field.type == 'password' || field.type == 'email') {
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label"; 
             html += (field.labelClass) ? " " + field.labelClass : "";
             html += "\" for=\"" + fld + '">';
             html += (field.icon) ? this.icon(field.icon) : "";
             html += field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             html += (field.clear) ? "<div class=\"input-append\">\n" : "";
             if (field.control === null || field.control === undefined || field.control) {
                html += "<input ";
                html += this.attr(field,'type');
                html += "ng-model=\"" + fld + '" ';
                html += 'name="' + fld + '" ';
                html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                html += (field.id) ? this.attr(field,'id') : "";
                html += (field.class) ? this.attr(field, 'class') : "";
                html += (field.placeholder) ? this.attr(field,'placeholder') : "";
                html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
                html += (options.mode == 'add' && field.addRequired) ? "required " : "";
                html += (field.readonly) ? "readonly " : "";
                html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                html += (field.capitalize) ? "capitalize " : "";
                html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled=\"" + field.associated + "_ask\" " : "";
                html += "/>";
                if (field.clear) {
                   html += " \n<button class=\"btn\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " + 
                       "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\"><i class=\"icon-undo\"></i></button>\n";
                   html += "</div>\n";
                }
                if (field.ask) {
                   html += " \n<label class=\"checkbox inline ask-checkbox\"><input type=\"checkbox\" ng-model=\"" + 
                       fld + "_ask\" ng-change=\"ask('" + fld + "','" + field.associated + "')\" /> Ask at runtime?</label>";
                }
                html += "<br />\n";
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
             }
             html += "</div>\n";
             html += "</div>\n";
           }
        }

       //textarea fields
       if (field.type == 'textarea') { 
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             html += "<textarea ";
             html += (field.rows) ? this.attr(field, 'rows') : "";
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             html += (field.class) ? this.attr(field,'class') : "";
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += (field.id) ? this.attr(field,'id') : "";
             html += (field.placeholder) ? this.attr(field,'placeholder') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly) ? "readonly " : "";
             html += "></textarea><br />\n";
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

       //select field
       if (field.type == 'select') { 
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             html += "<select ";
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             //html += "ng-options=\"item.label for item in " + fld + "_options\" "; 
             html += this.attr(field, 'ngOptions');
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += (field.id) ? this.attr(field,'id') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly) ? "readonly " : "";
             html += ">\n";  
             html += "<option value=\"\">Choose " + field.label + "</option>\n";
             html += "</select><br />\n";
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

       //number field
       if (field.type == 'number') { 
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             // Use 'text' rather than 'number' so that our integer directive works correctly
             html += "<input type=\"text\" value=\"" + field.default + "\" class=\"spinner\" ";
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             html += (field.min || field.min == 0) ? this.attr(field, 'min') : "";
             html += (field.max) ? this.attr(field, 'max') : "";
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += (field.id) ? this.attr(field,'id') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly) ? "readonly " : "";
             html += (field.integer) ? "integer " : "";
             html += "/><br />\n";
             // Add error messages
             if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
                html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</span>\n";
             }
             if (field.integer) {
                html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Must be an integer value</span>\n";
             }
             if (field.min || field.max) { 
                html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " + 
                    this.form.name + '_form.' + fld + ".$error.max\">Must be in range " + field.min + " to " + 
                    field.max + "</span>\n";
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

       if (field.type == 'hidden') {
          if ( (options.mode == 'edit' && field.includeOnEdit) ||
               (options.mode == 'add' && field.includeOnAdd) ) {
             html += "<input type=\"hidden\" ng-model=\"" + fld + "\" name=\"" + fld + "\" />";
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
          html += "<button class=\"lookup-btn btn\" " + this.attr(field,'ngClick') + "><i class=\"icon-search\"></i></button>\n";
          html += "<input class=\"input-medium\" type=\"text\" ";
          html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField +  "\" ";
          html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
          html += (field.ngChange) ? this.attr(field,'ngChange') : "";
          html += (field.id) ? this.attr(field,'id') : "";
          html += (field.placeholder) ? this.attr(field,'placeholder') : "";
          html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
          html += (options.mode == 'add' && field.addRequired) ? "required " : "";
          html += " awlookup />\n";
          html += "</div><br />\n";
          // Add error messages
          if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
             html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + 
                 field.sourceModel + '_' + field.sourceField  + ".$dirty && " + 
                 this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField + 
                 ".$error.required\">A value is required!</span>\n";
          }
          html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + 
              field.sourceModel + '_' + field.sourceField  + ".$dirty && " + 
              this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField  + 
              ".$error.awlookup\">Value not found</span>\n";
          html += "<span class=\"error api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField + 
              "_api_error\"></span>\n";
          html += "</div>\n";
          html += "</div>\n";
       }

       return html;
       },

    build: function(options) {
       //
       // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML 
       // string to be injected into the current view. 
       //
       var html = '';
       
       if (!this.modal) {
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
       }

       if ((!this.modal && this.form.statusFields)) {
          // Add status fields section (used in Jobs form)
          html += "<div class=\"well\">\n";
          if (this.form.statusActions) {
             html += "<div class=\"status-actions\">\n";
             var act;
             for (action in this.form.statusActions) {
                 act = this.form.statusActions[action];
                 html += "<button " + this.attr(act, 'ngClick') + 
                         "class=\"btn btn-small " + act.class + "\" ";
                 html += (act.awToolTip) ? this.attr(act,'awToolTip') : "";
                 html += (act.awToolTip) ? "data-placement=\"top\" " : "";
                 html += " >" + this.icon(act.icon) + "</button> ";
              }
              html += "</div>\n";
              html += "<div class=\"status-spin\"><i class=\"icon-spinner icon-spin\" ng-show=\"statusSearchSpin == true\"></i></div>\n";
          }
          for (var fld in this.form.statusFields) {
              field = this.form.statusFields[fld];
              html += this.buildField(fld, field, options);
          }
          html += "</div><!-- well -->\n";
       }

       if (this.form.fieldsAsHeader) {
          html += "<div class=\"well\">\n";
          html += "<form class=\"form-inline\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "\" novalidate >\n";
          for (var fld in this.form.fields) {
              field = this.form.fields[fld];
              html += this.headerField(fld, field, options);
          }
          html += "</form>\n";
          html += "</div>\n";
       }
       else { 
          // Start the well
          if ( this.has('well') ) {
             html += "<div class=\"well\">\n";
          }

          html += "<form class=\"form-horizontal\" name=\"" + this.form.name + '_form" id="' + this.form.name + '" novalidate>' + "\n";
          html += "<div ng-show=\"flashMessage != null && flashMessage != undefined\" class=\"alert alert-info\">{{ flashMessage }}</div>\n";

          var field;
          if (this.form.twoColumns) { 
             html += "<div class=\"row-fluid\">\n";
             html += "<div class=\"span6\">\n";
             for (var fld in this.form.fields) {
                 field = this.form.fields[fld];
                 if (field.column == 1) {
                    html += this.buildField(fld, field, options);
                 }
             }
             html += "</div><!-- column 1 -->\n";
             html += "<div class=\"span6\">\n";
             for (var fld in this.form.fields) {
                 field = this.form.fields[fld];
                 if (field.column == 2) {
                    html += this.buildField(fld, field, options);
                 }
             }
             html += "</div><!-- column 2 -->\n";
             html += "</div><!-- inner row -->\n";
          }
          else {
             // original, single-column form
             for (var fld in this.form.fields) {
                 var field = this.form.fields[fld];
                 html += this.buildField(fld, field, options);
             }
          }

          //buttons
          if (!this.modal) {
             if (this.has('buttons')) {
                html += (this.form.twoColumns) ? "<hr />" : "";
                html += "<div class=\"control-group\">\n";
                html += "<div class=\"controls buttons\">\n";
             }
             for (var btn in this.form.buttons) {
                 var button = this.form.buttons[btn];
                 //button
                 html += "<button ";
                 html += "class=\"btn"; 
                 html += (this.form.twoColumns) ? "" : " btn-small";
                 html += (button.class) ? " " + button.class : "";
                 html += "\" ";
                 if (button.ngClick) {
                    html += this.attr(button,'ngClick');
                 }
                 
                 if (button.ngDisabled) {
                    if (btn !== 'reset') {
                       html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid";
                       html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : ""; 
                       html += "\" ";
                    }
                    else {
                       html += "ng-disabled=\"" + this.form.name + "_form.$pristine";
                       html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : ""; 
                       html += "\" ";   
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
          }

          if ( this.has('well') ) {
             html += "</div>\n";
          }
       }


       if ((!this.modal && this.form.items)) {
          for (itm in this.form.items) {
              html += "<div class=\"well form-items\">\n";
              html += SearchWidget({ iterator: this.form.items[itm].iterator, template: this.form.items[itm], mini: false, label: 'Filter Events'});
              html += "<div class=\"item-count pull-right\">Viewing" + " \{\{ " + this.form.items[itm].iterator + "Page + 1 \}\} of " +
                  "\{\{ " + this.form.items[itm].iterator + "Count \}\}</div>\n";
              html += "<hr />\n";
              html += "<ul class=\"pager\">\n";
              html += "<li ng-class=\"" + this.form.items[itm].iterator + "PrevUrlDisable\"><a href=\"\" " +
                  "ng-click=\"prevSet('" + this.form.items[itm].set + "','" + this.form.items[itm].iterator + "')\">&larr; Prev</a></li>\n";
              html += "<li ng-class=\"" + this.form.items[itm].iterator + "NextUrlDisable\"><a href=\"\" " +
                  "ng-click=\"nextSet('" + this.form.items[itm].set + "','" + this.form.items[itm].iterator + "')\">&rarr; Next</a></li>\n";
              html +="</ul>\n";
              html += "<form class=\"form-horizontal\" name=\"" + this.form.name + '_items_form" id="' + this.form.name + '_items_form" novalidate>' + "\n";
              for (var fld in this.form.items[itm].fields) {
                  var field = this.form.items[itm].fields[fld];
                  html += this.buildField(fld, field, options);
              }
              html += "</form>\n";
              html += "<ul class=\"pager\">\n";
              html += "<li ng-class=\"" + this.form.items[itm].iterator + "PrevUrlDisable\"><a href=\"\" " +
                  "ng-click=\"prevSet('" + this.form.items[itm].set + "','" + this.form.items[itm].iterator + "')\">&larr; Prev</a></li>\n";
              html += "<li ng-class=\"" + this.form.items[itm].iterator + "NextUrlDisable\"><a href=\"\" " +
                  "ng-click=\"nextSet('" + this.form.items[itm].set + "','" + this.form.items[itm].iterator + "')\">&rarr; Next</a></li>\n";
              html +="</ul>\n";
              html += "</div><!-- well -->\n";
          }
       }
       
       if ((!this.modal) && options.related && this.form.related) {
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
           if (form.related[itm].type == 'collection' || form.related[itm].type == 'tree') {
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

              if (form.related[itm].instructions) {
                 html += "<div class=\"alert alert-info alert-block\">\n";
                 html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                 html += "<strong>Hint: </strong>" + form.related[itm].instructions + "\n";
                 html += "</div>\n"
              }

              if (form.related[itm].type == 'tree') {
                 html += "<div>\n";
                 // Add actions(s)
                 if (form.related[itm].actions && form.related[itm].actions.length > 0) {
                    html += "<div class=\"text-right actions\">\n";
                    for (var act in form.related[itm].actions) {
                        var action = form.related[itm].actions[act];
                        html += "<button class=\"btn btn-mini btn-success\" ";
                        html += this.attr(action,'ngClick');
                        html += (action.awToolTip) ? this.attr(action,'awToolTip') : "";
                        html += ">" + this.icon(action.icon) + "</button>\n";
                    }
                    html += "</div>\n";
                 }
                 html += "<div id=\"tree-view\"></div>\n";
                 html += "</div>\n";
              }
              else {
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
                  var rfield;
                  var base = (form.related[itm].base) ? form.related[itm].base : itm;
                  base = base.replace(/^\//,'');
                  for (var fld in form.related[itm].fields) {
                      cnt++;
                      rfield = form.related[itm].fields[fld];
                      html += "<td>";
                      if ((rfield.key || rfield.link || rfield.linkTo || rfield.ngClick )) {
                         if (rfield.linkTo) {
                            html += "<a href=\"#" + rfield.linkTo + "\">";
                         }
                         else if (rfield.ngClick) {
                            html += "<a href=\"\"" + this.attr(rfield, 'ngClick') + "\">";
                         }
                         else {
                            html += "<a href=\"#/" + base + "/{{" + form.related[itm].iterator + ".id }}\">";
                         }
                      }
                      html += "{{ " + form.related[itm].iterator + "." + fld + " }}";
                      if ((rfield.key || rfield.link || rfield.linkTo || rfield.ngClick )) {
                         html += "</a>";
                      }
                      html += "</td>\n";
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
              }

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