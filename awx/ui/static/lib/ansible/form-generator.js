/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * FormGenerator 
 * Pass in a form definition from FormDefinitions and out pops an html template.
 * See js/form-definitions.js for form example. For now produces a Twitter Bootstrap
 * horizontal form. 
 * 
 */

angular.module('FormGenerator', ['GeneratorHelpers', 'ngCookies'])
    .factory('GenerateForm', [ '$location', '$cookieStore', '$compile', 'SearchWidget', 'PaginateWidget', 'Attr', 'Icon', 'Column', 
    function($location, $cookieStore, $compile, SearchWidget, PaginateWidget, Attr, Icon, Column) {
    return {
    
    setForm: function(form) {
       this.form = form;
       },
 
    attr: Attr,

    icon: Icon,

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
          if (options.modal_body_id) {
             element = angular.element(document.getElementById(options.modal_body_id));
          }
          else {
             // use default dialog
             element = angular.element(document.getElementById('form-modal-body'));
          }
       }
       else {
          element = angular.element(document.getElementById('htmlTemplate'));
       }

       this.mode = options.mode;
       this.modal = (options.modal) ? true : false;
       
       this.setForm(form);
       element.html(this.build(options));  // Inject the html
       this.scope = element.scope();       // Set scope specific to the element we're compiling, avoids circular reference
                                           // From here use 'scope' to manipulate the form, as the form is not in '$scope'
       $compile(element)(this.scope);

       if ( ((!options.modal) && options.related) || this.form.forceListeners ) {
          this.addListeners();
       }

       if (options.mode == 'add') {
          this.applyDefaults();
       }

       if (options.modal) {
          this.scope.formHeader = (options.mode == 'add') ? form.addTitle : form.editTitle;  //Default title for default modal
          this.scope.formModalInfo = false  //Disable info button for default modal
          $('.popover').remove();  //remove any lingering pop-overs
          if (options.modal_selector) {
             $(options.modal_selector).removeClass('skinny-modal'); //Used in job_events to remove white space
             $(options.modal_selector).modal({ backdrop: 'static', keyboard: false });
          }
          else {
             $('#form-modal').removeClass('skinny-modal'); //Used in job_events to remove white space
             $('#form-modal').modal({ backdrop: 'static', keyboard: false });
          }
       }
       return this.scope;
       },

    applyDefaults: function() {
       for (fld in this.form.fields) {
           if (this.form.fields[fld]['default'] || this.form.fields[fld]['default'] == 0) {
              if (this.form.fields[fld].type == 'select' && this.scope[fld + '_options']) {
                 this.scope[fld] = this.scope[fld + '_options'][this.form.fields[fld]['default']];
              }
              else {
                 this.scope[fld] = this.form.fields[fld]['default'];
              }
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
           if (this.form.fields[fld].sourceModel) {
              this.scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField] = '';
              this.scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '_api_error'] = '';
           }
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

        if (this.modal) {
           $('.jqui-accordion-modal').accordion({
                collapsible: false,
                heightStyle: 'content',
                active: 0
                });
        }
        else {
           $('.jqui-accordion').each( function(index) {
              
               var active = false;
               var list = $cookieStore.get('accordions');
               var found = false;
               if (list) {
                  var id = $(this).attr('id');
                  var base = ($location.path().replace(/^\//,'').split('/')[0]);
                  for (var i=0; i < list.length && found == false; i++) {
                      if (list[i].base == base && list[i].id == id) {
                         found = true;
                        active = list[i].active; 
                      }
                  }
               }

               if (found == false && $(this).attr('data-open') == 'true') {
                  active = 0;
               }
              
               $(this).accordion({
                   collapsible: true,
                   heightStyle: 'content',
                   active: active,
                   activate: function( event, ui ) {
                       $('.jqui-accordion').each( function(index) {
                           var active = $(this).accordion('option', 'active');
                           var id = $(this).attr('id');
                           var base = ($location.path().replace(/^\//,'').split('/')[0]);
                           var list = $cookieStore.get('accordions');
                           if (list == null || list == undefined) {
                              list = [];
                           }
                           var found = false;
                           for (var i=0; i < list.length && found == false; i++) {
                               if ( list[i].base == base && list[i].id == id) {
                                  found = true; 
                                  list[i].active = active; 
                               }
                           }
                           if (found == false) {
                              list.push({ base: base, id: id, active: active });
                           }
                           $cookieStore.put('accordions',list);
                           });
                       }
                       });
                   });
          }
       },
     
    genID: function() {
       var id = new Date();
       return id.getTime();
       },

    headerField: function(fld, field, options) {
       var html = '';
       if (field.label) {
          html += "<label>" + field.label + "</label>\n";
       }
       html += "<input type=\"text\" name=\"" + fld + "\" ";
       html += "ng-model=\"" + fld + "\" ";
       html += (field['class']) ? this.attr(field, "class") : "";
       html += " readonly />\n";
       return html;
       },

    button: function(btn, topOrBottom) {
       // pass in a button object and get back an html string containing
       // a <button> element.
       var html = '';
       for (var i=0; i < btn.position.length; i++) {
           if (btn.position[i].indexOf(topOrBottom) >= 0) {
              html += "<button "; 
              html += "class=\"btn";
              html += (btn['class']) ?  " " + btn['class'] : "";
              if (btn.position[i] == 'top-right' || btn.position[i] == 'bottom-right') {
                 html += " " + "pull-right";  
              }
              html += "\" ";
              html += (btn.ngClick) ? this.attr(btn, 'ngClick') : "";
              html += ">" + this.attr(btn, 'icon');
              html += " " + btn.label;
              html += "</button>\n";
           }
       }
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
             html += (field.ngHide) ? this.attr(field,'ngHide') : "";
             html += ">\n";
             html += "<label class=\"control-label"; 
             html += (field.labelClass) ? " " + field.labelClass : "";
             html += "\" for=\"" + fld + '">';
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += (field.icon) ? this.icon(field.icon) : "";
             html += field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             html += (field.clear || field.genMD5) ? "<div class=\"input-append\">\n" : "";
             if (field.control === null || field.control === undefined || field.control) {
                html += "<input ";
                html += this.attr(field,'type');
                html += "ng-model=\"" + fld + '" ';
                html += 'name="' + fld + '" ';
                html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                html += (field.id) ? this.attr(field,'id') : "";
                html += (field['class']) ? this.attr(field, 'class') : "";
                html += (field.placeholder) ? this.attr(field,'placeholder') : "";
                html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
                html += (options.mode == 'add' && field.addRequired) ? "required " : "";
                html += (field.readonly || field.showonly) ? "readonly " : "";
                html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                html += (field.capitalize) ? "capitalize " : "";
                html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                    field.awRequiredWhen.variable + "\" " : "";
                html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled=\"" + field.associated + "_ask\" " : "";
                html += "/>";
                if (field.clear) {
                   html += " \n<button class=\"btn\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " + 
                       "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\"><i class=\"icon-undo\"></i></button>\n";
                   html += "</div>\n";
                }
                if (field.genMD5) {
                   html += " \n<button class=\"btn\" ng-click=\"genMD5('" + fld + "')\" " + 
                       "aw-tool-tip=\"Generate " + field.label + "\" data-placement=\"top\" id=\"" + fld + "-gen-btn\"><i class=\"icon-repeat\"></i></button>\n";
                   /*html += " \n<button style=\"margin-left: 10px;\" class=\"btn\" ng-click=\"selectAll('" + fld + "')\" " + 
                       "aw-tool-tip=\"Select " + field.label + " for copy\" data-placement=\"top\" id=\"" + fld + "-copy-btn\"><i class=\"icon-copy\"></i></button>\n";*/
                   html += "</div>\n";
                }
                if (field.ask) {
                   html += " \n<label class=\"checkbox inline ask-checkbox\"><input type=\"checkbox\" ng-model=\"" + 
                       fld + "_ask\" ng-change=\"ask('" + fld + "','" + field.associated + "')\" /> Ask at runtime?</label>";
                }
                html += "<br />\n";
                // Add error messages
                if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ||
                     field.awRequiredWhen ) {
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
             
             if (field.label !== false) {
                html += "<label class=\"control-label\" for=\"" + fld + '">';
                html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
                html += field.label + '</label>' + "\n";
                html += "<div class=\"controls\">\n";
             }

             // Variable editing
             if (fld == "variables" || fld == "extra_vars" || fld == 'inventory_variables') {
                html += "<div class=\"parse-selection\">Parse as: " +
                    "<label class=\"radio inline\"><input type=\"radio\" ng-model=\"";
                html += (this.form.parseTypeName) ? this.form.parseTypeName : 'parseType'; 
                html += "\" value=\"yaml\"> YAML</label>\n";
                html += "<label class=\"radio inline\"><input type=\"radio\" ng-model=\"";
                html += (this.form.parseTypeName) ? this.form.parseTypeName : 'parseType';
                html += "\" value=\"json\"> JSON</label></div>\n";
             }
             
             html += "<textarea ";
             html += (field.rows) ? this.attr(field, 'rows') : "";
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             html += (field['class']) ? this.attr(field,'class') : "";
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += (field.id) ? this.attr(field,'id') : "";
             html += (field.placeholder) ? this.attr(field,'placeholder') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly || field.showonly) ? "readonly " : "";
             html += "></textarea><br />\n";
             // Add error messages
             if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
                html += "<span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</span>\n";
             }
             html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
             if (field.label !== false) {
                html += "</div>\n";
             }
             html += "</div>\n";
          }
       }

       //select field
       if (field.type == 'select') { 
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label\" for=\"" + fld + '">';
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += field.label + '</label>' + "\n";
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
             html += "<label class=\"control-label\" for=\"" + fld + '">';
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             // Use 'text' rather than 'number' so that our integer directive works correctly
             html += (field.slider) ? "<div class=\"slider\" id=\"" + fld + "-slider\"></div>\n" : "";
             html += "<input type=\"text\" value=\"" + field['default'] + "\" ";
             html += (field['class']) ? this.attr(field, 'class') : "";
             html += (field.slider) ? "ng-slider=\"" + fld + "\" " : ""; 
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             html += (field.min || field.min == 0) ? this.attr(field, 'min') : "";
             html += (field.max) ? this.attr(field, 'max') : "";
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += (field.slider) ? "id=\"" + fld + "-number\"" : (field.id) ? this.attr(field,'id') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly) ? "readonly " : "";
             html += (field.integer) ? "integer " : "";
             html += "/>\n";
             html += "<br />\n";
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
             html += (field.readonly) ? "disabled " : "";
             html += " /> " + field.label + "\n";
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += "</label>\n";
             html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
             html += "</div>\n";
             html += "</div>\n";
          }
       }

       //radio
       if (field.type == 'radio') {
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\" "
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label\" for=\"" + fld + '">';
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += field.label + '</label>' + "\n";
             html += "<div class=\"controls\">\n";
             for (var i=0; i < field.options.length; i++) {
                 html += "<label class=\"radio inline\" ";
                 html += (field.options[i].ngShow) ? this.attr(field.options[i],'ngShow') : "";
                 html += ">";
                 html += "<input type=\"radio\" "; 
                 html += "name=\"" + fld + "\" ";
                 html += "value=\"" + field.options[i].value + "\" ";
                 html += "ng-model=\"" + fld + "\" ";
                 html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                 html += (field.readonly) ? "disabled " : "";
                 html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
                 html += (options.mode == 'add' && field.addRequired) ? "required " : "";
                 html += " /> " + field.options[i].label + "\n";
                 html += "</label>\n";
             }
             if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
                html += "<p><span class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</span></p>\n";
             }
             html += "<p><span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span></p>\n";
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
       if (field.type == 'lookup' && (field.excludeMode == undefined || field.excludeMode != options.mode)) {
          html += "<div class=\"control-group\""
          html += (field.ngShow) ? this.attr(field,'ngShow') : "";
          html += ">\n";
          html += "<label class=\"control-label\" for=\"" + fld + '">';
          html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
          html +=  field.label + '</label>' + "\n";
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
          html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
              field.awRequiredWhen.variable + "\" " : "";
          html += " awlookup />\n";
          html += "</div><br />\n";
          // Add error messages
          if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ||
               field.awRequiredWhen ) {
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

       //text fields
       if (field.type == 'custom') {
          if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {
             html += "<div class=\"control-group\""
             html += (field.ngShow) ? this.attr(field,'ngShow') : "";
             html += ">\n";
             html += "<label class=\"control-label"; 
             html += (field.labelClass) ? " " + field.labelClass : "";
             html += "\" for=\"" + fld + '">';
             html += (field.awPopOver) ? this.attr(field, 'awPopOver') : "";
             html += (field.icon) ? this.icon(field.icon) : "";
             html += (field.label) ? field.label : '';
             html += '</label>' + "\n";
             html += "<div class=\"controls\">\n"; 
             html += field.control;
             html += "</div>\n";
             html += "</div>\n";
           }
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
                 html += "<button " + this.attr(act, 'ngClick') + "class=\"btn btn-small";
                 html += (act['class']) ? " " + act['class'] : "";
                 html += "\" ";
                 html += (act.awToolTip) ? this.attr(act,'awToolTip') : "";
                 html += (act.awToolTip) ? "data-placement=\"top\" " : "";
                 html += " >" + this.icon(act.icon);
                 html += (act.label) ? act.label : ""; 
                 html += "</button> ";
              }
              html += "</div>\n";
              html += "<div class=\"status-spin\"><i class=\"icon-spinner icon-spin\" ng-show=\"statusSearchSpin == true\"></i></div>\n";
          }
          html += "<div class=\"status-fields\">\n";
          for (var fld in this.form.statusFields) {
              field = this.form.statusFields[fld];
              html += this.buildField(fld, field, options);
          }
          html += "</div><!-- status fields -->\n";
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
          
          if ( this.form.collapse && this.form.collapseMode == options.mode) {
             html += "<div id=\"" + this.form.name + "-collapse-0\" ";
             html += (this.form.collapseOpen) ? "data-open=\"true\" " : "";
             html += "class=\"jqui-accordion\">\n";
             html += "<h3>" + this.form.collapseTitle + "</h3>\n"; 
             html += "<div>\n";
          }

          if (this.form.navigation) {
             html += "<div class=\"navigation-buttons navigation-buttons-top\">\n";
             for (btn in this.form.navigation) {
                 var btn = this.form.navigation[btn];
                 if ( btn.position.indexOf('top-left') >= 0 || btn.position.indexOf('top-right') >= 0 ) {
                    html += this.button(btn, 'top');
                 }
             }
             html += "</div>\n";
          }
          
          // Start the well
          if ( this.has('well') ) {
             html += "<div class=\"well\">\n";
          }

          html += "<form class=\"form-horizontal";
          html += (this.form['class']) ? ' ' + this.form['class'] : '';
          html += "\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "\" autocomplete=\"false\" novalidate>\n";
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
             var section = '';             
             for (var fld in this.form.fields) {
                 var field = this.form.fields[fld];
                 if (field.section && field.section != section) {
                    if (section !== '') {
                       html += "</div>\n";
                    }
                    else {
                        html += "</div>";
                        html += "<div id=\"" + this.form.name + "-collapse\" class=\"jqui-accordion-modal\">\n";
                    }
                    var sectionShow = (this.form[field.section + 'Show']) ? " ng-show=\"" + this.form[field.section + 'Show'] + "\"" : "";
                    html += "<h3" + sectionShow + ">" + field.section + "</h3>\n"; 
                    html += "<div" + sectionShow + ">\n";
                    section = field.section;
                 }
                 html += this.buildField(fld, field, options);
             }
             if (section !== '') {
                html += "</div>\n</div>\n";
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
                 html += "class=\"btn btn-small";
                 html += (button['class']) ? " " + button['class'] : "";
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

          if (this.form.navigation) {
             html += "<div class=\"navigation-buttons navigation-buttons-bottom\">\n";
             for (btn in this.form.navigation) {
                 var btn = this.form.navigation[btn];
                 if ( btn.position.indexOf('bottom-left') >= 0 || btn.position.indexOf('bottom-right') >= 0 ) {
                    html += this.button(btn, 'bottom');
                 }
             }
             html += "</div>\n";
          }

          if ( this.form.collapse && this.form.collapseMode == options.mode ) {
             html += "</div>\n";
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
       
       if (this.form.name == 'inventory' && options.mode == 'edit') {
          html += this.buildTree(options);
       }
       else {
          if ((!this.modal) && options.related && this.form.related) {
             html += this.buildCollections(options);
          }
       }

       return html;
     
       },

    buildTree: function(options) {
       //
       // Used to create the inventory detail view
       //
       var idx = 1;
       var form = this.form;
       
      /* var html = "<div class=\"accordion-group\">\n";
       html += "<div class=\"accordion-heading\">\n";
       html += "<a id=\"" + form.name + "-collapse-2\" class=\"accordion-toggle\" data-toggle=\"collapse\" data-parent=\"#accordion\" href=\"#collapse2\">";
       html += "<i class=\"icon-angle-up icon-white\"></i>Inventory Content</a>\n";
       html += "</div>\n";
       html += "<div id=\"collapse2\" class=\"accordion-body collapse in\">\n";
       html += "<div class=\"accordion-inner\">\n";
       */
       html = "<div id=\"" + this.form.name + "-collapse-2\" data-open=\"true\" class=\"jqui-accordion\">\n";
       html += "<h3>Inventory Content<h3>\n"; 
       html += "<div>\n";
       
       for (var itm in form.related) {
           if (form.related[itm].type == 'tree') {
              html += "<div class=\"span5\">";
              html += "<div class=\"inventory-buttons\">";
              html += "<button ng-click=\"addGroup()\" ng-hide=\"groupAddHide\" id=\"inv-group-add\" " + 
                  "class=\"btn btn-mini btn-success\" aw-tool-tip=\"Add a new group\" " +
                  "data-placement=\"bottom\"><i class=\"icon-plus\"></i> Add Group</button>";
              html += "<button ng-click=\"editGroup()\" ng-hide=\"groupEditHide\" id=\"inv-group-edit\" class=\"btn btn-mini btn-success\" " +
                  "aw-tool-tip=\"Edit the selected group\" data-placement=\"bottom\" " +
                  "<i class=\"icon-edit\"></i> Edit Group</button>";
              html += "<button ng-click=\"deleteGroup()\" ng-hide=\"groupDeleteHide\" id=\"inv-group-delete\" " +
                  "aw-tool-tip=\"Delete the selected group\" data-placement=\"bottom\" " +
                  "class=\"btn btn-mini btn-danger\">" +
                  "<i class=\"icon-remove\"></i> Delete Group</button>";
              html += "</div>\n";  
              html += "<div id=\"tree-view\"></div>\n";
              html += "<div class=\" inventory-filter\">";
              html += "<span ng-show=\"has_active_failures == true\"><label class=\"checkbox inline\">";
              html += "<input ng-model=\"inventoryFailureFilter\" ng-change=\"filterInventory()\" type=\"checkbox\"" +
                  ">Show only groups with failures</label></span></div>\n";
              html += "</div>\n";
           }
           else {
              html += "<div id=\"group-view\" class=\"span7\">\n";
              html += "<div id=\"hosts-well\" class=\"well\">\n";
              html += "<h4 id=\"hosts-title\">" + form.related[itm].title + "</h4>\n";
              html += SearchWidget({ iterator: form.related[itm].iterator, template: form.related[itm], mini: true });

              // Add actions(s)
              html += "<div class=\"list-actions\">\n";
              for (var action in form.related[itm].actions) {
                  html += "<button class=\"btn btn-mini ";
                  html += (form.related[itm].actions[action]['class']) ? form.related[itm].actions[action]['class'] : "btn-success";
                  html += "\" ";
                  html += (form.related[itm]['actions'][action].id) ? this.attr(form.related[itm]['actions'][action],'id') : "";
                  html += this.attr(form.related[itm]['actions'][action],'ngClick');
                  html += (form.related[itm]['actions'][action].awToolTip) ? this.attr(form.related[itm]['actions'][action],'awToolTip') : "";
                  html += (form.related[itm]['actions'][action].awToolTip) ? "data-placement=\"top\" " : "";
                  html += (form.related[itm]['actions'][action].ngHide) ? this.attr(form.related[itm]['actions'][action],'ngHide') : "";
                  html += "><i class=\"" + form.related[itm]['actions'][action].icon + "\"></i>";
                  html += (form.related[itm]['actions'][action].label) ?  " " + form.related[itm]['actions'][action].label : ""; 
                  html += "</button>\n";
              }
              html += "</div>\n";
             
              // Start the list
              html += "<div class=\"list\">\n";
              html += "<table class=\"" + form.related[itm].iterator + " table table-condensed table-hover\">\n";
              html += "<thead>\n";
              html += "<tr>\n";
              html += "<th>#</th>\n";
              for (var fld in form.related[itm].fields) {
                  html += "<th class=\"list-header\" id=\"" + form.related[itm].iterator + '-' + fld + "-header\" " +
                       "ng-click=\"sort('" + form.related[itm].iterator + "', '" + fld + "')\">" +
                       form.related[itm]['fields'][fld].label;
                  html += " <i class=\"";
                  if (form.related[itm].fields[fld].key) {
                     if (form.related[itm].fields[fld].desc) {
                        html += "icon-sort-down";
                     }
                     else {
                        html += "icon-sort-up";
                     }
                  }
                  else {
                     html += "icon-sort";
                  }
                  html += "\"></i></a></th>\n";
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
                  html += Column({ list: form.related[itm], fld: fld, options: options, base: base })
              }
             
              // Row level actions
              html += "<td class=\"actions\">";
              for (action in form.related[itm].fieldActions) {
                  html += "<button class=\"btn btn-mini"; 
                  html += (form.related[itm]['fieldActions'][action]['class']) ?
                      " " + form.related[itm]['fieldActions'][action]['class'] : "";
                  html += "\" ";
                  html += (form.related[itm]['fieldActions'][action].awToolTip) ? this.attr(form.related[itm]['fieldActions'][action],'awToolTip') : "";
                  html += this.attr(form.related[itm]['fieldActions'][action],'ngClick') +
                      ">" + this.icon(form.related[itm]['fieldActions'][action].icon);
                  html += (form.related[itm].fieldActions[action].label) ?  " " + form.related[itm].fieldActions[action].label : ""; 
                  html += "</button> ";
              }
              html += "</td>";
              html += "</tr>\n";
              
              // Message for when a related collection is empty
              html += "<tr class=\"info\" ng-show=\"" + form.related[itm].iterator + "Loading == false && (" + itm + " == null || " + itm + ".length == 0)\">\n";
              html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No records matched your search.</div></td>\n";
              html += "</tr>\n";

              // Message for loading
              html += "<tr class=\"info\" ng-show=\"" + form.related[itm].iterator + "Loading == true\">\n";
              html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">Loading...</div></td>\n";
              html += "</tr>\n";

              // End List
              html += "</tbody>\n";
              html += "</table>\n";
              html += "</div>\n";    // close well
              html += "</div>\n";    // close group-view

              html += PaginateWidget({ set: itm, iterator: form.related[itm].iterator, mini: true });      
           }
           idx++;
       }
       
       html += "</div>\n";
       html += "</div>\n";
       //html += "</div>\n"; 
       
       return html; 
       },

    buildCollections: function(options) {
       //
       // Create TB accordians with imbedded lists for related collections
       // Should not be called directly. Called internally by build().
       //
       var idx = 1;
       var form = this.form;
       html = "<div id=\"" + this.form.name + "-collapse-" + idx + "\" class=\"jqui-accordion\">\n";
       for (var itm in form.related) {
           if (form.related[itm].type == 'collection') {

              // Start the accordion group
             /* html += "<div class=\"accordion-group\">\n";
              html += "<div class=\"accordion-heading\">\n";
              html += "<a id=\"" + form.name + "-collapse-" + idx + "\" class=\"accordion-toggle\" data-toggle=\"collapse\" data-parent=\"#accordion\" href=\"#collapse" + idx + "\">";
              html += "<i class=\"icon-angle-down icon-white\"></i>" + form.related[itm].title + "</a>\n";
              html += "</div>\n";
              html += "<div id=\"collapse" + idx + "\" class=\"accordion-body collapse";
              if (form.related[itm].open) {
                 html += " in";   //open accordion on load
              }
              html += "\">\n";
              html += "<div class=\"accordion-inner\">\n";
              */
             
              
              html += "<h3>" + form.related[itm].title + "<h3>\n"; 
              html += "<div>\n";

              if (form.related[itm].instructions) {
                 html += "<div class=\"alert alert-info alert-block\">\n";
                 html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                 html += "<strong>Hint: </strong>" + form.related[itm].instructions + "\n";
                 html += "</div>\n"
              }

              html += "<div class=\"well\">\n";
              html += SearchWidget({ iterator: form.related[itm].iterator, template: form.related[itm], mini: true });

              // Add actions(s)
              html += "<div class=\"list-actions\">\n";
              for (var act in form.related[itm].actions) {
                 var action = form.related[itm].actions[act];
                 html += "<button class=\"btn btn-small ";
                 html += (form.related[itm].actions[act]['class']) ? form.related[itm].actions[act]['class'] : "btn-success";
                 html += "\" ";
                 html += this.attr(action,'ngClick');
                 html += (action.awToolTip) ? this.attr(action,'awToolTip') : "";
                 html += (action.awToolTip) ? "data-placement=\"right\" " : "";
                 html += "><i class=\"" + action.icon + "\"></i>";
                 html += (action.label) ? " " + action.label : "";
                 html += "</button>\n";
              }
              html += "</div>\n";

              // Start the list
              html += "<div class=\"list\">\n";
              html += "<table class=\"" + form.related[itm].iterator + " table table-condensed table-hover\">\n";
              html += "<thead>\n";
              html += "<tr>\n";
              html += (form.related[itm].index == undefined || form.related[itm].index !== false) ? "<th>#</th>\n" : "";
              for (var fld in form.related[itm].fields) {
                 html += "<th class=\"list-header\" id=\"" + form.related[itm].iterator + '-' + fld + "-header\" " +
                     "ng-click=\"sort('" + form.related[itm].iterator + "', '" + fld + "')\">" +
                     form.related[itm]['fields'][fld].label;
                 html += " <i class=\"";
                 //html += (form.related[itm].fields[fld].key) ? "icon-sort-up" : "icon-sort";
                 if (form.related[itm].fields[fld].key) {
                    if (form.related[itm].fields[fld].desc) {
                       html += "icon-sort-down";
                    }
                    else {
                       html += "icon-sort-up";
                    }
                 }
                 else {
                    html += "icon-sort";
                 }
                 html += "\"></i></a></th>\n";
              }
              html += "<th></th>\n";
              html += "</tr>\n";
              html += "</thead>";
              html += "<tbody>\n";

              html += "<tr ng-repeat=\"" + form.related[itm].iterator + " in " + itm + "\" >\n";
              if (form.related[itm].index == undefined || form.related[itm].index !== false) {
                html += "<td>{{ $index + (" + form.related[itm].iterator + "Page * " + 
                    form.related[itm].iterator + "PageSize) + 1 }}.</td>\n";
              }
              var cnt = 1;
              var rfield;
              var base = (form.related[itm].base) ? form.related[itm].base : itm;
              base = base.replace(/^\//,'');
              for (var fld in form.related[itm].fields) {
                 cnt++;
                 html += Column({ list: form.related[itm], fld: fld, options: options, base: base });
              }

              // Row level actions
              html += "<td class=\"actions\">";
              for (act in form.related[itm].fieldActions) {
                 var action = form.related[itm].fieldActions[act];
                 html += "<button class=\"btn btn-small"; 
                 html += (action['class']) ? " " + action['class'] : "";
                 html += "\" " + this.attr(action,'ngClick');
                 html += (action.awToolTip) ? this.attr(action,'awToolTip') : "";
                 html += (action.awToolTip) ? "data-placement=\"top\" " : "";
                 html += ">" + this.icon(action.icon);
                 html += (action.label) ?  " " + action.label : ""; 
                 html += "</button> ";
              }
              html += "</td>";
              html += "</tr>\n";

              // Message for when a related collection is empty
              html += "<tr class=\"info\" ng-show=\"" + form.related[itm].iterator + "Loading == false && (" + itm + " == null || " + itm + ".length == 0)\">\n";
              html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No records matched your search.</div></td>\n";
              html += "</tr>\n";

              // Message for loading
              html += "<tr class=\"info\" ng-show=\"" + form.related[itm].iterator + "Loading == true\">\n";
              html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">Loading...</div></td>\n";
              html += "</tr>\n";

              // End List
              html += "</tbody>\n";
              html += "</table>\n";
              html += "</div>\n";    // close well
              html += "</div>\n";    // close list div

              html += PaginateWidget({ set: itm, iterator: form.related[itm].iterator, mini: true });      

              // End Accordion
              html += "</div>\n";    // accordion inner

              idx++;
            }
       }
       html += "</div>\n";    // accordion body
       html += "</div>\n";

       return html; 
       }
       
}}]);