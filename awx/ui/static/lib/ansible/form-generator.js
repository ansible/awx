/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 * FormGenerator 
 * Pass in a form definition from FormDefinitions and out pops an html template.
 * See js/form-definitions.js for form example. For now produces a Twitter Bootstrap
 * horizontal form. 
 * 
 */

angular.module('FormGenerator', ['GeneratorHelpers', 'ngCookies', 'Utilities'])
    .factory('GenerateForm', ['$rootScope', '$location', '$cookieStore', '$compile', 'SearchWidget', 'PaginateWidget', 'Attr',
        'Icon', 'Column', 'NavigationLink', 'HelpCollapse', 'Button', 'DropDown', 'Empty',
    function($rootScope, $location, $cookieStore, $compile, SearchWidget, PaginateWidget, Attr, Icon, Column, NavigationLink,
        HelpCollapse, Button, DropDown, Empty) {
    return {
    
    setForm: function(form) {
       this.form = form;
       },
 
    attr: Attr,

    icon: Icon,

    accordion_count: 0,

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
          if (options.id) {
             element = angular.element(document.getElementById(options.id));
          }
          else {
             element = angular.element(document.getElementById('htmlTemplate'));
          }
       }

       this.mode = options.mode;
       this.modal = (options.modal) ? true : false;
       this.setForm(form);

       // Inject the html
       if (options.buildTree) {
          element.html(this.buildTree(options));
       }
       else if (options.html) {
          element.html(options.html);
       }
       else {
          element.html(this.build(options));
       }
       
       if (options.scope) {
          this.scope = options.scope;
       }
       else {
          this.scope = element.scope();
       }

       $compile(element)(this.scope);
 
       if (!options.buildTree && !options.html) {
          // Reset the scope to prevent displaying old data from our last visit to this form
          for (var fld in form.fields) {
              this.scope[fld] = null;
          }
          for (var set in form.related) {
              this.scope[set] = null;
          }
          if ( ((!options.modal) && options.related) || this.form.forceListeners ) {
             this.addListeners();
          }
          if (options.mode == 'add') {
             this.applyDefaults();
          }
       }

       // Remove any lingering tooltip and popover <div> elements
       $('.tooltip').each( function(index) {
           $(this).remove();
           });
       
       $('.popover').each(function(index) {
              // remove lingering popover <div>. Seems to be a bug in TB3 RC1
              $(this).remove();
              });
       
       $(window).unbind('resize');

       // Prepend an asterisk to required field label
       $('.form-control[required], input[type="radio"][required]').each(function() {
            if ( Empty($(this).attr('aw-required-when')) ) {
                var label = $(this).parent().parent().find('label').first();
                if ($(this).attr('type') == 'radio') {
                   label = $(this).parent().parent().parent().find('label').first();
                }
                if (label.length > 0) {
                   var span = label.children('span');
                   if (span.length > 0 && !span.first().hasClass('prepend-asterisk')) {
                      span.first().addClass('prepend-asterisk');
                   }
                   else if (span.length <= 0 && !label.first().hasClass('prepend-asterisk')) {
                      label.first().addClass('prepend-asterisk');
                   }
                }
            }
            });

       try {
           $('#help-modal').empty().dialog('destroy');
       }
       catch(e) {  
           //ignore any errors should the dialog not be initialized 
       }

       if (options.modal) {
          this.scope.formModalActionDisabled = false;
          this.scope.formModalInfo = false  //Disable info button for default modal
          if (form) {
             if (options.modal_title_id) {
                this.scope[options.modal_title_id] = (options.mode == 'add') ? form.addTitle : form.editTitle;
             }
             else {
                this.scope.formModalHeader = (options.mode == 'add') ? form.addTitle : form.editTitle;  //Default title for default modal       
             }
          }
          if (options.modal_selector) {
             $(options.modal_selector).modal({ show: true, backdrop: 'static', keyboard: true });
             $(options.modal_selector).on('shown.bs.modal', function() {
                 $(options.modal_select + ' input:first').focus();
                 });
             $(options.modal_selector).unbind('hidden.bs.modal');
          }
          else {
             $('#form-modal').modal({ show: true, backdrop: 'static', keyboard: true });
             $('#form-modal').on('shown.bs.modal', function() {
                 $('#form-modal input:first').focus();
                 });
             $('#form-modal').on('hidden.bs.modal');
          }
          $(document).bind('keydown', function(e) {
              if (e.keyCode === 27) {
                 if (options.modal_selector) {
                    $(options.modal_selector).modal('hide');
                 }
                 $('#prompt-modal').modal('hide');
                 $('#form-modal').modal('hide');
              }
              });
       }
       if (!this.scope.$$phase) {
          this.scope.$digest();
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
        // value, you have to clear the model.

        if (this.scope[this.form.name + '_form']) {
            this.scope[this.form.name + '_form'].$setPristine();
        }

        for (var fld in this.form.fields) {
            if (this.form.fields[fld].type == 'checkbox_group') {
              for (var i=0; i < this.form.fields[fld].fields.length; i++) {
                  this.scope[this.form.fields[fld].fields[i].name] = '';
                  this.scope[this.form.fields[fld].fields[i].name + '_api_error'] = '';
              }
            }
            else {
              this.scope[fld] = '';      
              this.scope[fld + '_api_error'] = '';  
            }
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
            //if (this.scope.fields[fld].awPassMatch) {
            //   this.scope[this.form.name + '_form'][fld].$setValidity('awpassmatch', true); 
            //}
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
           this.scope.accordionToggle = function(selector) {
               $(selector).collapse('toggle');
               if ( $(selector + '-icon').hasClass('icon-minus') ) {
                  $(selector + '-icon').removeClass('icon-minus').addClass('icon-plus');
               }
               else {
                  $(selector + '-icon').removeClass('icon-plus').addClass('icon-minus')
               }
               }

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

    clearApiErrors: function() {
       for (fld in this.form.fields) {
           if (this.form.fields[fld].sourceModel) {
              this.scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '_api_error'] = '';
           }
           else {
              this.scope[fld + '_api_error'] = '';  
           }
       }
       if (!this.scope.$$phase) {
          this.scope.$digest();
       } 
       },

    button: Button,

    navigationLink: NavigationLink,

    
    buildHelpCollapse: function(collapse_array) {
        var html = ''; 
        var params = {};
        for (var i=0; i < collapse_array.length; i++) {
            params.hdr = collapse_array[i].hdr; 
            params.content = collapse_array[i].content; 
            params.idx = this.accordion_count++;
            params.show = (collapse_array[i].show) ? collapse_array[i].show : null;   
            html += HelpCollapse(params);       
        }
        return html;
        },

    
    buildField: function(fld, field, options, form) {

       function getFieldWidth() {
           var x;
           if (form.formFieldSize) {
              x = form.formFieldSize;
           }
           else if (field.xtraWide) {
              x = "col-lg-10";
           }
           else if (field.column) {
              x = "col-lg-8";
           }
           else if (!form.formFieldSize && options.modal) {
              x = "col-lg-10";
           }
           else {
              x = "col-lg-6";
           }
           return x;
       }

       function getLabelWidth() {
           var x;
           if (form.formLabelSize) {
              x = form.formLabelSize;
           }
           else if (field.column) {
              x = "col-lg-4";
           }
           else if (!form.formLabelSize && options.modal) {
              x = "col-lg-2";
           }
           else {
              x = "col-lg-2";
           }
           return x;
           }

       function buildId(field, fld, form) {
           var html = '';
           if (field.id) {
              html += Attr(field,'id');
           }
           else {
              html += "id=\"" + form.name + "_" + fld + "\" ";
           }
           return html;
           }

       function buildCheckbox(form, field, fld, idx, includeLabel) {
           var html = '';
           var label = (includeLabel !== undefined && includeLabel == false) ? false : true;
           
           if (label) {
               html += "<label class=\"";
               html += (field.inline == undefined || field.inline == true) ? "checkbox-inline" : "";
               html += (field.labelClass) ? " " + field.labelClass : "";
               html += "\">";
           }
           
           html += "<input type=\"checkbox\" "; 
           html += (!label) ? "style=\"padding-top:5px;\" " : "";
           html += Attr(field,'type');
           html += "ng-model=\"" + fld + '" ';
           html += "name=\"" + fld + '" ';
           html += (field.ngChange) ? Attr(field,'ngChange') : "";
           html += "id=\"" + form.name + "_" +  fld + "_chbox\" ";
           html += (idx !== undefined) ? "_" + idx : "";
           html += "class=\"";
           html += (field['class']) ? field['class'] + " " : "";
           html += (!label) ? "checkbox-no-label" : "";
           html += "\"";
           html += (field.trueValue !== undefined) ? Attr(field,'trueValue') : "";
           html += (field.falseValue !== undefined) ? Attr(field,'falseValue') : "";
           html += (field.checked) ? "checked " : "";
           html += (field.readonly) ? "disabled " : "";
           html += " > ";

           if (label) {
               html += field.label + " ";
               html += (field.awPopOver) ? Attr(field, 'awPopOver', fld) : "";
               html += "</label>\n";
           }

           return html;
           }
       
       var html = '';

       if (field.type == 'alertblock') {
          html += "<div class=\"alert ";
          html += (field.closeable == undefined || field.closeable == true) ? "alert-dismissable " : "";
          html += field['class'] + "\" "; 
          html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
          html += ">\n";
          html += (field.closeable == undefined || field.closeable == true) ? 
              "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-hidden=\"true\">&times;</button>\n" : "";
          html += field.alertTxt;
          html += "</div>\n";
       }

       if (field.type == 'hidden') {
          if ( (options.mode == 'edit' && field.includeOnEdit) ||
               (options.mode == 'add' && field.includeOnAdd) ) {
             html += "<input type=\"hidden\" ng-model=\"" + fld + "\" name=\"" + fld + "\" />";
          }
       }
       
       if ( (! field.readonly) || (field.readonly && options.mode == 'edit') ) {  
          html += "<div class=\"form-group\" ";
          html += (field.ngShow) ? this.attr(field,'ngShow') : "";
          html += (field.ngHide) ? this.attr(field,'ngHide') : "";
          html += ">\n";      

          //text fields
          if (field.type == 'text' || field.type == 'password' || field.type == 'email') {
             html += "<div class=\"label-text " + getLabelWidth();
             html += (field.labelClass) ? " " + field.labelClass : "";
             html += "\" ";
             html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
             html += ">\n";
             html += (field.awPopOver && !field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
             html += "<label ";
             html += "class=\"control-label";
             html += "\" ";
             html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
             html += "for=\"" + fld + '">';
             html += (field.icon) ? this.icon(field.icon) : "";
             html += "<span class=\"label-text\">" + field.label + '</span></label>' + "\n";
             html += (field.awPopOver && field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
             html += "</div>\n";
             html += "<div ";
             html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : "";
             html += "class=\"" + getFieldWidth() + "\">\n";
             html += (field.clear || field.genMD5) ? "<div class=\"input-group\">\n" : "";
             if (field.control === null || field.control === undefined || field.control) {
                html += "<input ";
                html += this.attr(field,'type');
                html += "ng-model=\"" + fld + '" ';
                html += 'name="' + fld + '" ';
                html += (field.ngChange) ? this.attr(field,'ngChange') : "";
                html += (field.chkPass) ? "chk-pass " : "";
                html += buildId(field, fld, this.form);
                html += "class=\"form-control";
                html += (field['class']) ? " " + this.attr(field, 'class') : "";
                html += "\" ";
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
                html += (field.awValidUrl) ? "aw-valid-url " : ""; 
                html += (field.associated && this.form.fields[field.associated].ask) ? "ng-disabled=\"" + field.associated + "_ask\" " : "";
                html += (field.awMultiselect) ? "aw-multiselect=\"" + field.awMultiselect + "\" " : "";
                html += " >\n";
             }
             
             if (field.clear) {
                html += "<span class=\"input-group-btn\"><button type=\"button\" ";
                html += "id=\"" + this.form.name + "_" + fld + "_clear_btn\" "; 
                html += "class=\"btn btn-default\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " + 
                   "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\" ";
                html += (field.ask) ? "ng-disabled=\"" + fld + "_ask\" " : "";
                html += " ><i class=\"icon-undo\"></i></button>\n";
                html += "</span>\n</div>\n";
                if (field.ask) {
                   html += "<label class=\"checkbox-inline ask-checkbox\">";
                   html += "<input type=\"checkbox\" ng-model=\"" + 
                       fld + "_ask\" ng-change=\"ask('" + fld + "','" + field.associated + "')\" ";
                   html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                   html += "> Ask at runtime?</label>";
                }
             }
             
             if (field.genMD5) {
                html += "<span class=\"input-group-btn\"><button type=\"button\" class=\"btn btn-default\" ng-click=\"genMD5('" + fld + "')\" " + 
                   "aw-tool-tip=\"Generate " + field.label + "\" data-placement=\"top\" id=\"" + this.form.name + "_" + fld + "_gen_btn\">" +
                   "<i class=\"icon-magic\"></i></button></span>\n</div>\n";
             }
             
             // Add error messages
             if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ||
                field.awRequiredWhen ) {
                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
             }
             if (field.type == "email") {
                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
                this.form.name + '_form.' + fld + ".$error.email\">A valid email address is required!</div>\n";
             }
             if (field.awPassMatch) {
                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + 
                    ".$error.awpassmatch\">Must match Password value</div>\n";
             }
             if (field.awValidUrl) {
                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + 
                    ".$error.awvalidurl\">URL must begin with ssh, http or https and may not contain '@'</div>\n";
             }
             
             html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

             if (field.chkPass) {
                // complexity error
                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + 
                    ".$error.complexity\">Password must be stronger</div>\n";
                
                // progress bar
                html += "<div class=\"pw-progress\">\n";
                html += "<div class=\"progress progress-striped\">\n";
                html += "<div id=\"progbar\" class=\"progress-bar\" role=\"progress\"></div>\n";
                html += "</div>\n";
                
                // help panel
                html += HelpCollapse({
                    hdr: 'Password Complexity',
                    content: "<p>A password with reasonable strength is required. As you type the password " + 
                    "a progress bar will measure the strength. Sufficient strength is reached when the bar turns green.</p>" +
                    "<p>Password strength is judged using the following:</p>" +
                    "<ul class=\"pwddetails\">" + 
                    "<li>Minimum 8 characters in length</li>\n" +
                    "<li>Contains a sufficient combination of the following items:\n" +
                    "<ul>\n" +
                    "<li>UPPERCASE letters</li>\n" +
                    "<li>Numbers</li>\n" +
                    "<li>Symbols _!@#$%^&*()</li>\n" +
                    "</ul>\n" +
                    "</li>\n" +
                    "</ul>\n",
                    idx: this.accordion_count++,
                    show: null
                    });
                html += "</div><!-- pw-progress -->\n";
             }

             // Add help panel(s)
             html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

             html += "</div>\n";
         }

         //textarea fields
         if (field.type == 'textarea') { 
             
            if (field.label !== false) {
               html += "<div class=\"label-text " + getLabelWidth();
               html += (field.labelClass) ? " " + field.labelClass : "";
               html += "\" ";
               html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
               html += ">\n";
               html += (field.awPopOver && !field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
               html += "<label class=\"control-label\" ";
               html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
               html += "for=\"" + fld + "\">";
               html += field.label + '</label>' + "\n";
               html += (field.awPopOver && field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
               html += "</div>\n";
               html += "<div ";
               html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
               html += "class=\"" + getFieldWidth() + "\">\n";
            }

            // Variable editing
            if (fld == "variables" || fld == "extra_vars" || fld == 'inventory_variables' || fld == 'source_vars') {
              html += "<div class=\"parse-selection\" id=\"" + this.form.name + "_" + fld + "_parse_type\">Parse as: " +
                  "<input type=\"radio\" ng-model=\"";
              html += (field.parseTypeName) ? field.parseTypeName : 'parseType'; 
              html += "\" value=\"yaml\"> <span class=\"parse-label\">YAML</span>\n";
              html += "<input type=\"radio\" ng-model=\"";
              html += (field.parseTypeName) ? field.parseTypeName : 'parseType';
              html += "\" value=\"json\"> <span class=\"parse-label\">JSON</span>\n</div>\n";
            }

            html += "<textarea ";
            html += (field.rows) ? this.attr(field, 'rows') : "";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += "class=\"form-control";
            html += (field['class']) ? " " + field['class'] : "";
            html += "\" ";
            html += (field.ngChange) ? this.attr(field,'ngChange') : "";
            html += buildId(field, fld, this.form);
            html += (field.placeholder) ? this.attr(field,'placeholder') : "";
            html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
            html += (options.mode == 'add' && field.addRequired) ? "required " : "";
            html += (field.readonly || field.showonly) ? "readonly " : "";
            html += "></textarea>\n";
            // Add error messages
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
              this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
            }
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            if (field.label !== false) {
              html += "</div>\n";
            }
         }

         //select field
         if (field.type == 'select') {
            html += "<div class=\"label-text " + getLabelWidth();
            html += (field.labelClass) ? " " + field.labelClass : "";
            html += "\" ";
            html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
            html += ">\n";
            html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
            html += "<label class=\"control-label\" for=\"" + fld + '">';
            html += field.label + '</label>' + "\n";
            html += "</div>\n";
            html += "<div ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n";
            html += "<select ";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += "class=\"form-control";
            html += (field['class']) ? " " + field['class'] : "";
            html += "\" ";
            html += this.attr(field, 'ngOptions');
            html += (field.ngChange) ? this.attr(field,'ngChange') : "";
            html += buildId(field, fld, this.form);
            html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
            html += (options.mode == 'add' && field.addRequired) ? "required " : "";
            html += (field.multiSelect) ? "multiple " : "";
            html += (field.readonly) ? "readonly " : "";
            html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                  field.awRequiredWhen.variable + "\" " : "";
            html += ">\n";
            html += "<option value=\"\">";
            html += (field.defaultOption) ? field.defaultOption : "Choose " + field.label;
            html += "</option>\n";
            html += "</select>\n";
            // Add error messages
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired)  ||
                 field.awRequiredWhen ) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
              this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
            }
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            
            // Add help panel(s)
            html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';
            
            html += "</div>\n";
         }

         //number field
         if (field.type == 'number') { 
            html += "<label class=\"control-label " + getLabelWidth() + "\" for=\"" + fld + '">';
            html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
            html += field.label + '</label>' + "\n";
            html += "<div ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n";
            // Use 'text' rather than 'number' so that our integer directive works correctly
            html += (field.slider) ? "<div class=\"slider\" id=\"" + fld + "-slider\"></div>\n" : "";
            html += "<input "; 
            html += (field.spinner) ? "" : "type=\"text\" ";
            html += "\" value=\"" + field['default'] + "\" ";
            html += "class=\"form-control";
            html += (field['class']) ? " " + field['class'] : "";
            html += "\" ";
            html += (field.slider) ? "ng-slider=\"" + fld + "\" " : ""; 
            html += (field.spinner) ? "ng-spinner=\"" + fld + "\" " : ""; 
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += buildId(field, fld, this.form);
            html += (field.min || field.min == 0) ? this.attr(field, 'min') : "";
            html += (field.max) ? this.attr(field, 'max') : "";
            html += (field.ngChange) ? this.attr(field,'ngChange') : "";
            html += (field.slider) ? "id=\"" + fld + "-number\"" : (field.id) ? this.attr(field,'id') : "";
            html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
            html += (options.mode == 'add' && field.addRequired) ? "required " : "";
            html += (field.readonly) ? "readonly " : "";
            html += (field.integer) ? "integer " : "";
            html += (field.disabled) ? "data-disabled=\"true\" " : "";
            html += " >\n";
            // Add error messages
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
              this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
            }
            if (field.integer) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Must be an integer value</div>\n";
            }
            if (field.min !== undefined || field.max !== undefined) { 
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " + 
                  this.form.name + '_form.' + fld + ".$error.max\">Must be an integer between " + field.min + " and ";
              html += (field.max !== undefined) ? field.max : 'unlimited';
              html += "</div>\n";
            }
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            html += "</div>\n";
         } 
         
         //checkbox group
         if (field.type == 'checkbox_group') {
            html += "<label class=\"control-label " + getLabelWidth() + "\">" + 
                field.label + "</label>\n";
            html += "<div class=\"checkbox-group ";
            html += getFieldWidth();
            html += "\" ";
            html += "id=\"" + this.form.name + "_" + fld + "_chbox_group\" "; 
            html += ">\n";
            for (var i=0; i < field.fields.length; i++) {
                html += buildCheckbox(this.form, field.fields[i], field.fields[i].name, i);
            }
            // Add error messages
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
              this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
            }
            if (field.integer) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Must be an integer value</div>\n";
            }
            if (field.min || field.max) { 
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " + 
                  this.form.name + '_form.' + fld + ".$error.max\">Must be in range " + field.min + " to " + 
                  field.max + "</div>\n";
            }
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            html += "</div>\n";
         }

         //checkbox
         if (field.type == 'checkbox') {
            html += "<div class=\"label-text " + getLabelWidth();
            html += (field.labelClass) ? " " + field.labelClass : "";
            html += "\" ";
            html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
            html += ">\n";
            html += (field.awPopOver && !field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
            html += "<label ";
            html += "class=\"control-label";
            html += "\" ";
            html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
            html += "for=\"" + fld + '">';
            html += (field.icon) ? this.icon(field.icon) : "";
            html += '<span class=\"label-text\">' + field.label + '</span></label>' + "\n";
            html += (field.awPopOver && field.awPopOverRight) ? this.attr(field, 'awPopOver', fld) : "";
            html += "</div>\n";
            html += "<div ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n"; 
            html += buildCheckbox(this.form, field, fld, undefined, false);
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            html += "</div>\n"
         }

         //radio
         if (field.type == 'radio') {
            html += "<label class=\"control-label " + getLabelWidth() + "\" for=\"" + fld + '">';
            html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
            html += '<span class=\"label-text\">' + field.label + '</span></label>' + "\n";
            html += "<div ";
            html += "id=\"" + this.form.name + "_" + fld + "_radio_grp\" ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n"; 
            for (var i=0; i < field.options.length; i++) {
               html += "<label class=\"radio-inline\" ";
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
               html += (field.ngDisabled) ? this.attr(field,'ngDisabled') : "";
               html += " > " + field.options[i].label + "\n";
               html += "</label>\n";
            }
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ) {
              html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " + 
              this.form.name + '_form.' + fld + ".$error.required\">A value is required!</div>\n";
            }
            html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
            html += "</div>\n";
         }

         //lookup type fields
         if (field.type == 'lookup' && (field.excludeMode == undefined || field.excludeMode != options.mode)) {
            html += "<div class=\"label-text " + getLabelWidth();
            html += (field.labelClass) ? " " + field.labelClass : "";
            html += "\" ";
            html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
            html += "id=\"" + this.form.name + "_" + fld + "_lookup\" ";
            html += ">\n";
            html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
            html += "<label class=\"control-label\" for=\"" + fld + '">';
            html +=  field.label + '</label>' + "\n";
            html += "</div>\n";
            html += "<div ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n";
            html += "<div class=\"input-group\">\n";
            html += "<span class=\"input-group-btn\">\n";
            html += "<button type=\"button\" class=\"lookup-btn btn btn-default\" " + this.attr(field,'ngClick') + "><i class=\"icon-search\"></i></button>\n";
            html += "</span>\n";
            html += "<input type=\"text\" class=\"form-control input-medium lookup\" ";
            html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField +  "\" ";
            html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
            html += "class=\"form-control\" ";
            html += (field.ngChange) ? this.attr(field,'ngChange') : "";
            html += (field.id) ? this.attr(field,'id') : "";
            html += (field.placeholder) ? this.attr(field,'placeholder') : "";
            html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
            html += (field.awRequiredWhen) ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" aw-required-when=\"" +
                field.awRequiredWhen.variable + "\" " : "";
            html += " awlookup >\n";
            html += "</div>\n";
            // Add error messages
            if ( (options.mode == 'add' && field.addRequired) || (options.mode == 'edit' && field.editRequired) ||
                 field.awRequiredWhen ) {
               html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + 
                   field.sourceModel + '_' + field.sourceField  + ".$dirty && " + 
                   this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField + 
                   ".$error.required\">A value is required!</div>\n";
            }
            html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + 
                field.sourceModel + '_' + field.sourceField  + ".$dirty && " + 
                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField  + 
                ".$error.awlookup\">Value not found</div>\n";
            html += "<div class=\"error api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField + 
                "_api_error\"></div>\n";
            html += "</div>\n";
         }

         //custom fields
         if (field.type == 'custom') {
            html += "<div class=\"label-text " + getLabelWidth();
            html += (field.labelClass) ? " " + field.labelClass : "";
            html += "\" ";
            html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
            html += ">\n";
            html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
            html += "<label class=\"control-label\" for=\"" + fld + '">';
            html += (field.icon) ? this.icon(field.icon) : "";
            html += (field.label) ? field.label : '';
            html += '</label>' + "\n";
            html += "</div>\n";
            html += "<div ";
            html += "id=\"" + form.name + "_" + fld + "\" ";
            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : ""; 
            html += "class=\"" + getFieldWidth() + "\">\n"; 
            html += field.control;
            html += "</div>\n";
         }

         if (field.type == 'lgtextarea') {
             // Use for modal, readonly textarea fields
             html += "<div class=\"label-text " + getLabelWidth() + "\">\n";
             html += "<label class=\"control-label\">";
             html += (field.icon) ? this.icon(field.icon) : "";
             html += (field.label) ? field.label : '';
             html += "</label>";
             html += "</div>\n";
             html += "<div class=\"col-lg-12\">\n";
             html += "<div style=\"padding-left:10px;\">"
             html += "<textarea ";
             html += (field.rows) ? this.attr(field, 'rows') : "";
             html += "ng-model=\"" + fld + '" ';
             html += 'name="' + fld + '" ';
             html += "class=\"form-control";
             html += (field['class']) ? " " + field['class'] : "";
             html += "\" ";
             html += (field.ngChange) ? this.attr(field,'ngChange') : "";
             html += buildId(field, fld, this.form);
             html += (field.placeholder) ? this.attr(field,'placeholder') : "";
             html += (options.mode == 'edit' && field.editRequired) ? "required " : "";
             html += (options.mode == 'add' && field.addRequired) ? "required " : "";
             html += (field.readonly || field.showonly) ? "readonly " : "";
             html += "></textarea>\n";
             html += "</div>\n";
             html += "</div>\n";
         }

         html += "</div>\n";

       }
       return html;
       },

    getActions: function(options) {
        // Use to add things like Activity Stream to a detail page  
        html = "<div class=\"list-actions\">\n";
        for (action in this.form.actions) {
            if (this.form.actions[action].mode == 'all' || this.form.actions[action].mode == options.mode) {
                html += this.button(this.form.actions[action], action);
            }
        }
        html += "</div>\n";
        return html;
        },

    /*
    activityCrumbs: function() {
       // Breadcrumbs for activity stream widget
       // Make the links clickable using ng-click function so we can first remove the stream widget.
       html = '';
       html += "<div class=\"nav-path\">\n";
       html += "<ul class=\"breadcrumb\">\n";
       html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"\" ng-click=\"{{ crumb.ngClick }}\">{{ crumb.title | capitalize }}</a></li>\n";
       html += "<li class=\"active\">";
       html += this.form.editTitle;
       html += "</li>\n</ul>\n</div>\n";
       return html;
       },
       */

    breadCrumbs: function(options, navigation) {
       var html = '';
       
       html += "<div class=\"nav-path\">\n";
       html += "<ul class=\"breadcrumb\">\n";
       html += "<li ng-repeat=\"crumb in breadcrumbs\"><a href=\"{{ '#' + crumb.path }}\">{{ crumb.title | capitalize }}</a></li>\n";
       
       if (navigation) {
          
          var paths = $location.path().replace(/^\//,'').split('/');

          if (paths.length == 2) {
             html += "<li class=\"active\">";
             if (options.mode == 'edit') {
                html += this.form.editTitle;
             }
             else {
                html += this.form.addTitle; 
             }
             html += "</li>\n";
          }
          
          html += "<li class=\"active\"> </li>\n";
          html += "</ul>\n";
          html += "<div class=\"dropdown\">\n";
          for (var itm in navigation) {
              if (navigation[itm].active) {
                 html += "<a href=\"\" class=\"toggle\" ";
                 html += "data-toggle=\"dropdown\" ";
                 html += ">" + navigation[itm].label + " <i class=\"icon-chevron-sign-down crumb-icon\"></i></a>";
                 break;
              }
          }
    
          html += "<ul class=\"dropdown-menu\" role=\"menu\">\n";
          for (var itm in navigation) {
              html += "<li role=\"presentation\"><a role=\"menuitem\" tabindex=\"-1\" href=\"" +
                  navigation[itm].href + "\" ";
              // html += (navigation[itm].active) ? "class=\"active\" " : "";
              html += ">";
              html += "<i class=\"icon-ok\" style=\"visibility: ";
              html += (navigation[itm].active) ? "visible" : "hidden";
              html += "\"></i> ";
              html += (navigation[itm].listLabel) ? navigation[itm].listLabel : navigation[itm].label;
              html += "</a></li>\n";
          }
          html += "</ul>\n";
          html += "</div><!-- dropdown -->\n";
          html += "</div><!-- nav-path -->\n";
       }
       else {
          html += "<li class=\"active\">";
          if (options.mode == 'edit') {
             html += this.form.editTitle;
          }
          else {
             html += this.form.addTitle; 
          }
          html += "</li>\n</ul>\n</div><!-- nav-path -->\n";
       }
       return html;
       },

    build: function(options) {
       //
       // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML 
       // string to be injected into the current view. 
       //
       var html = '';
       
       if (!this.modal && (options.breadCrumbs == undefined || options.breadCrumbs == true)) {
          if (this.form.navigationLinks) {
             html += this.breadCrumbs(options, this.form.navigationLinks);
          }
          else {
             html += this.breadCrumbs(options);
          }
       }
 
       if ((!this.modal && this.form.statusFields)) {
          // Add status fields section (used in Jobs form)
          html += "<div class=\"well\">\n";
          if (this.form.statusActions) {
             html += "<div class=\"list-actions\">\n";
             var act;
             for (action in this.form.statusActions) {
                 act = this.form.statusActions[action];
                 html += this.button(act, action);
             }
             html += "</div>\n";
             //html += "<div class=\"status-spin\"><i class=\"icon-spinner icon-spin\" ng-show=\"statusSearchSpin == true\"></i></div>\n";
          }
          html += "<div class=\"form-horizontal status-fields\">\n";
          for (var fld in this.form.statusFields) {
              field = this.form.statusFields[fld];
              html += this.buildField(fld, field, options, this.form);
          }
          html += "</div><!-- status fields -->\n";
          html += "</div><!-- well -->\n";
       }

       if (this.form.fieldsAsHeader) {
          html += "<div class=\"well\">\n";
          html += "<form class=\"form-inline\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "_form\" novalidate >\n";
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
          
          // Start the well
          if ( !this.modal && this.has('well') ) {
             html += "<div class=\"well\">\n";
          }

          if (!this.modal && this.form.actions) {
              html += this.getActions(options);
          }

          // Add a title and optionally a close button (used on Inventory->Groups)
          if ( (!options.modal) && this.form.showTitle ) {
             html += "<div class=\"form-title\">";
             html += (options.mode == 'edit') ? this.form.editTitle : this.form.addTitle;
             if (this.has('titleActions')) {
                html += "<div class=\"title-actions pull-right\">\n";
                for (btn in this.form.titleActions) {
                    html += this.button(this.form.titleActions[btn]);
                }
                html += "</div>\n";
             }
             html += "</div>\n";
             html += "<hr class=\"form-title-hr\">\n";
          }

          html += "<form class=\"form-horizontal";
          html += (this.form['class']) ? ' ' + this.form['class'] : '';
          html += "\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "_form\" autocomplete=\"off\" novalidate>\n";
          html += "<div ng-show=\"flashMessage != null && flashMessage != undefined\" class=\"alert alert-info\">{{ flashMessage }}</div>\n";

          var field;
          if (this.form.twoColumns) { 
             html += "<div class=\"row\">\n";
             html += "<div class=\"col-lg-6\">\n";
             for (var fld in this.form.fields) {
                 field = this.form.fields[fld];
                 if (field.column == 1) {
                    html += this.buildField(fld, field, options, this.form);
                 }
             }
             html += "</div><!-- column 1 -->\n";
             html += "<div class=\"col-lg-6\">\n";
             for (var fld in this.form.fields) {
                 field = this.form.fields[fld];
                 if (field.column == 2) {
                    html += this.buildField(fld, field, options, this.form);
                 }
             }
             html += "</div><!-- column 2 -->\n";
             html += "</div>\n";
          }
          else {
             // original, single-column form
             var section = '';        
             var group = '';     
             for (var fld in this.form.fields) {
                 var field = this.form.fields[fld];
                 if  (!(options.modal && field.excludeModal)) {
                     if (field.group && field.group != group) {
                        if (group !== '') {
                           html += "</div>\n";
                        }
                        html += "<div class=\"well\">\n";
                        html += "<h5>" + field.group + "</h5>\n"; 
                        group = field.group;
                     }
                     if (field.section && field.section != section) {
                        if (section !== '') {
                           html += "</div>\n";
                        }
                        else {
                            html += "</div>\n";
                            html += "<div id=\"" + this.form.name + "-collapse\" class=\"jqui-accordion-modal\">\n";
                        }
                        var sectionShow = (this.form[field.section + 'Show']) ? " ng-show=\"" + this.form[field.section + 'Show'] + "\"" : "";
                        html += "<h3" + sectionShow + ">" + field.section + "</h3>\n"; 
                        html += "<div" + sectionShow + ">\n";
                        section = field.section;
                     }
                     html += this.buildField(fld, field, options, this.form);
                 }
             }
             if (section !== '') {
                html += "</div>\n</div>\n";
             }
             if (group !== '') {
                html += "</div>\n";
             }
          }

          //buttons
          if (!this.modal) {
             if (this.has('buttons')) {
                
                if (this.form.twoColumns) {
                   html += "<div class=\"row\">\n";
                   html += "<div class=\"col-lg-12\">\n";
                   html += "<hr />\n";
                }
                
                html += "<div class=\"form-group buttons\" ";
                html += "id=\"" + this.form.name + "_controls\" ";
                html += ">\n";
                html += "<label class=\"";
                html += (this.form.buttons['labelClass']) ? this.form.buttons['labelClass'] : "col-lg-2";
                html += " control-label\"> </label>\n";
                html += "<div class=\"";
                html += (this.form.buttons['controlClass']) ? this.form.buttons['controlClass'] : "col-lg-6"; 
                html += " controls\">\n";
                for (var btn in this.form.buttons) {
                    if (typeof this.form.buttons[btn] == 'object') {
                       var button = this.form.buttons[btn];
                       //button
                       html += "<button type=\"button\" ";
                       html += "class=\"btn btn-sm";
                       html += (button['class']) ? " " + button['class'] : "";
                       html += "\" ";
                       html += "id=\"" + this.form.name + "_" + btn + "_btn\" "; 
                       
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
                } 
                html += "</div>\n";
                html += "</div>\n";
                if (this.form.twoColumns) {
                   html += "</div>\n";
                   html += "</div>\n";
                }
             }
          }
          html += "</form>\n";
          
          if ( !this.modal && this.has('well') ) {
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
                  html += this.buildField(fld, field, options, this.form);
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
          html += this.buildCollections(options);
       }

       return html;
     
       },

    buildTree: function(options) {
       //
       // Used to create the inventory detail view
       //

       var form = this.form;
       var itm = "groups";
       var html = '';
       var navigation = {
            inventory: {
                href: "/#/inventories/{{ inventory_id }}",
                label: "Properties",
                icon: "icon-edit"
                },
            hosts: {
                href: "/#/inventories/{{ inventory_id }}/hosts",
                label: 'Hosts',  
                icon: 'icon-laptop'
                },
            groups: {
                href: "/#/inventories/{{ inventory_id }}/groups",
                label: 'Groups',  
                icon: 'icon-sitemap'
                }
            };
       
       if (form.type == 'groupsview') {
          navigation.inventory.active = false; 
          navigation.hosts.active = false;
          navigation.groups.active = true; 
          html += this.breadCrumbs(options, navigation);
          html += "<div class=\"row\">\n";
          html += "<div class=\"col-lg-4\" id=\"search-tree-target\">\n" +
                  "<div class=\"search-tree well\">\n" +
                  "<div id=\"search-tree-container\"></div>\n" +
                  "</div><!-- search-tree well -->\n" + 
                  "</div>\n";
          html += "<div class=\"col-lg-8 tree-form-container\">\n";
          html += "<div id=\"tree-form\">\n</div>\n";
          html += "</div>\n";
          html += "</div><!-- row -->\n";
       }
       else {
          // build the hosts page
          navigation.inventory.active = false; 
          navigation.hosts.active = true;
          navigation.groups.active = false; 
          html += this.breadCrumbs(options, navigation);
          html += "<div class=\"row\">\n";
          html += "<div class=\"col-lg-4\" id=\"search-tree-target\">\n";
          html += "<div class=\"search-tree well\">\n";
          html += "<div id=\"search-tree-container\">\n</div><!-- search-tree-container -->\n";
          html += "</div><!-- search-tree well -->\n";
          html += "</div><!-- col-lg-4 -->\n";
          html += "<div class=\"col-lg-8\">\n"; 
          html += "<div class=\"hosts-well well\">\n";
          html += SearchWidget({ iterator: form.iterator, template: form, mini: true, size: 'col-md-5 col-lg-5'});
          html += "<div class=\"col-md-6 col-lg-6\">\n"
          html += "<div class=\"list-actions\">\n";
          
          // Add actions(s)
          for (var action in form.actions) {
              html += this.button(form.actions[action], action);
          }
          html += "</div><!-- list-actions -->\n";
          html += "</div>\n";
          html += "</div><!-- row -->\n";
          html += "<div class=\"title\" ng-bind=\"groupTitle\"></div>\n";
          
          // Start the list
          html += "<div class=\"list\">\n";
          html += "<table id=\"hosts_table\" class=\"" + form.iterator + " table table-condensed table-hover\">\n";
          html += "<thead>\n";
          html += "<tr>\n";
          
          for (var fld in form.fields) {
              if (form.fields[fld].searchOnly == undefined || form.fields[fld].searchOnly == false) {
                  html += "<th class=\"list-header\" id=\"" + fld + "-header\" ";
                  html += (!form.fields[fld].nosort) ? "ng-click=\"sort('"+ fld + "')\"" : "";
                  html += ">";
                  html += (form['fields'][fld].label && form['fields'][fld].type !== 'DropDown') ? form['fields'][fld].label : '';
                  if (form.fields[fld].nosort == undefined || form.fields[fld].nosort == false) {
                     html += " <i class=\"";
                     if (form.fields[fld].key) {
                        if (form.fields[fld].desc) {
                           html += "icon-sort-down";
                        }
                        else {
                           html += "icon-sort-up";
                        }
                     }
                     else {
                        html += "icon-sort";
                     }
                     html += "\"></i>";
                  }
                  html += "</th>\n";
              }
          }

          html += "<th></th>\n";
          html += "</tr>\n";
          html += "</thead>";
          html += "<tbody>\n";
                
          html += "<tr ng-repeat=\"" + form.iterator + " in hosts\" >\n";

          // Select checkbox
          //html += "<td><input type=\"checkbox\" ng-model=\"" + form.iterator + ".selected\" ng-change=\"toggleOneHost()\" ></td>";
          
          var cnt = 0;
          var rfield; 

          for (var fld in form.fields) {
              cnt++;
              rfield = form.fields[fld];
              if (fld == 'groups' ) {
                 // generate group form control/button widget
                 html += "<td class=\"col-lg-5 col-md-4 col-sm-3\">";
                 html += "<div class=\"input-group input-group-sm\">\n";
                 html += "<span class=\"input-group-btn\">\n";
                 html += "<button class=\"btn btn-default\" type=\"button\" id=\"edit_groups_btn\" ng-click=\"editHostGroups({{ host.id }})\" " +
                     "aw-tool-tip=\"Edit group associations\" data-placement=\"top\" >" + 
                     "<i class=\"icon-sitemap\"></i></button>\n";
                 html += "</span>\n";
                 html += "<input type=\"text\" id=\"host_groups\" ng-model=\"host.groups\" class=\"form-control\" disabled=\"disabled\" >\n";
                 html += "</div>\n";
                 html += "</td>\n";
              }
              else {
                if (form.fields[fld].searchOnly == undefined || form.fields[fld].searchOnly == false) {
                   html += Column({ list: form, fld: fld, options: options, base: null });
                }
              }
          }
          
          // Row level actions
          html += "<td class=\"actions\">";
          for (act in form.fieldActions) {
             var action = form.fieldActions[act];
             if (action.type && action.type == 'DropDown') {
                html += DropDown({ field: action, td: false });
             }
             else {
                html += "<button type=\"button\" ";
                html += "id=\"row_" + act + "_btn\" ";
                html += "class=\"btn"; 
                html += (action['class']) ? " " + action['class'] : "";
                html += "\" " + this.attr(action,'ngClick');
                html += (action.awToolTip) ? this.attr(action,'awToolTip') : "";
                html += (action.awToolTip) ? "data-placement=\"top\" " : "";
                html += ">" + this.icon(action.icon);
                html += (action.label) ?  " " + action.label : ""; 
                html += "</button> ";
             }
          }
          html += "</td>";
          html += "</tr>\n";
          cnt++;
        
          // Message for when a related collection is empty
          html += "<tr class=\"info\" ng-show=\"" + form.iterator + "Loading == false && (hosts == null || hosts.length == 0)\">\n";
          html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">No records matched your search.</div></td>\n";
          html += "</tr>\n"; 

          // Message for loading
          html += "<tr class=\"info\" ng-show=\"HostsLoading == true\">\n";
          html += "<td colspan=\"" + cnt + "\"><div class=\"alert alert-info\">Loading...</div></td>\n";
          html += "</tr>\n";

          // End List
          html += "</tbody>\n";
          html += "</table>\n";
          html += "</div>\n";    // close list

          /*
          html += "<div class=\"row host-failure-filter\">\n";
          html += "<div class=\"col-lg-12\">\n";
          html += "<label class=\"checkbox-inline pull-right\"><input type=\"checkbox\" ng-model=\"hostFailureFilter\" ng-change=\"filterHosts()\" > Only show hosts with failed jobs" +
              "</label>\n";
          html += "</div>\n";
          html += "</div>\n";
          */

          html += "</div>\n";    // close well

          html += PaginateWidget({ set: 'hosts', iterator: form.iterator, mini: true }); 

          html += "</div>\n";
          html += "</div>\n";

          //html += "</div><!-- inventory-hosts -->\n";
        
        }
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
              html += "<h3 class=\"" + itm + "_collapse\">" + form.related[itm].title + "<h3>\n"; 
              html += "<div>\n";

              if (form.related[itm].instructions) {
                 html += "<div class=\"alert alert-info alert-block\">\n";
                 html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                 html += "<strong>Hint: </strong>" + form.related[itm].instructions + "\n";
                 html += "</div>\n"
              }

              html += "<div class=\"well\">\n";
              html += SearchWidget({ iterator: form.related[itm].iterator, template: form.related[itm], mini: true });
 
              html += "<div class=\"col-lg-8\">\n";
              html += "<div class=\"list-actions\">\n";
              for (var act in form.related[itm].actions) {
                 var action = form.related[itm].actions[act];
                 html += "<button type=\"button\" class=\"btn btn-xs ";
                 html += (form.related[itm].actions[act]['class']) ? form.related[itm].actions[act]['class'] : "btn-success";
                 html += "\" ";
                 html += "id=\"" + itm + "_" + act + "_btn\" ";
                 html += this.attr(action,'ngClick');
                 html += (action['ngShow']) ? this.attr(action,'ngShow') : "";
                 html += (action.awToolTip) ? this.attr(action,'awToolTip') : "";
                 html += (action.awToolTip) ? "data-placement=\"top\" " : "";
                 html += "><i class=\"" + action.icon + "\"></i>";
                 html += (action.label) ? " " + action.label : "";
                 html += "</button>\n";
              }
              html += "</div>\n";
              html += "</div>\n";
              html += "</div><!-- row -->\n"
              
              // Start the list
              html += "<div class=\"list\">\n";
              html += "<table id=\"" + itm + "_table" + "\" class=\"" + form.related[itm].iterator + " table table-condensed table-hover\">\n";
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
                 html += "<button type=\"button\" class=\"btn btn-xs"; 
                 html += (action['class']) ? " " + action['class'] : "";
                 html += "\" "; 
                 html += "id=\"row" + act + "_btn\" ";
                 html += this.attr(action,'ngClick');
                 html += (action.ngShow) ? this.attr(action, 'ngShow') : "";
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