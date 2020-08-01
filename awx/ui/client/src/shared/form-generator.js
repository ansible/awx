/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


  /**
 *  @ngdoc function
 *  @name shared.function:form-generator
 *  @description
 *
 * Generate form HTML from a form object. Form objects are found in /forms.
 *
 * #Generate and Inject Form
 *
 * To generate a form and inject it into the DOM the default method call is:
 *
 * ```
 * GenerateForm.inject(form, { mode: 'edit', related: true, scope: $scope});
 * ```
 * Expects 2 parameters where the first is a reference to a form object, and the second is an object of key/value parameter pairs. Returns the $scope object associated with the generated HTML.
 *
 * Parameters that can be passed:
 *
 * | Parameter | Required | Description |
 * | --------- | -------- | ----------- |
 * | html |  | String of HTML to be injected. Overrides HTML that would otherwise be generated using the form object. (Not sure if this is actually used anywhere.) |
 * | id | | The ID attribute value of the DOM elment that will receive the generated HTML. If provided, form generator will inject the HTML it genertates into the DOM element identified by the string value provided. Do not preceed the value with '#' |
 * | mode | Y | 'add', 'edit' or 'modal'. Use add when creating new data - creating a new orgranization, for example. Use edit when modifying existing data. Modal is deprecated. Use the 'id' option to inject a form into a modal dialog. |
 * | scope |  | Reference to $scope object. Will be passed to $compile and associated with any angular directives contained within the generated HTML. |
 * | showButtons | | true or false. If false, buttons defined in the buttons object will not be included in the generated HTML. |
 *
 * #Generate HTML Only
 *
 * To generate the HTML only and not inject it into the DOM use the buildHTML() method:
 *
 * ```
 * GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });
 * ```
 *
 * Pass the same parameters as above. Returns a string containing the generated HTML.
 *
 * #Reset Form
 *
 * Call GenerateFrom.reset() to clear user input, remove error messages and return the angular form object back to a pristine state. This is should be called when the user clicks the Reset button.
 *
 * #Form definitions
 *
 * See forms/*.js for examples.
 *
 * The form object can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | collapse | true or false. If true, places the form inside a jQueryUI accordion |
 * | collapseMode | 'add' or 'edit'. If the value of the mode parameter passed into .inject() or .buildHTML() matches collapseMode, the &lt;form&gt; will be placed in an accordion. |
 * | collapseOpen |  true or false. If true, the accordion will be open the first time the user views the form, or if no state information is found in local storage for the accordion. Subsequent views will depend on accordion state found in local storage. Each time user opens/closes an accordion the state is saved in local storage. |
 * | collapseOpenFirst | true or false. If true, the collapse will be open everytime the accordion is viewed, regardless of state data found in local storage. |
 * | collapseTitle | Text to use in the &lt;h3&gt; element of the accordion. Typically this will be 'Properties' |
 * | name | Name to give the form object. Used to create the id and name attribute values in the <form> element. |
 * | showActions | true or false. By default actions found in the actions object will be displayed at the top of the page. If set to false, actions will not be displayed. |
 * | twoColumns | true or false. By default fields are placed in a single vertical column following the Basic Example in the [Bootstrap form documentation](http://getbootstrap.com/css/#forms). Set to true for a 2 column layout as seen on the Job Templates detail page.|
 * | well | true or false. If true, wraps the with &lt;div class=&quot;aw-form-well&quot;&gt;&lt;/div&gt; |
 *
 * The form object will contain a fields object to hold the definiation of each field in the form. Attributes on a field object determine the HTML generated for the actual &lt;input&gt; or &lt;textarea&gt; element. Fields can have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | awPopOver | Adds aw-pop-over directive. Set to a string containing the text or html to be evaluated by the directive. |
 * | awPopOverWatch | Causes the awPopOver directive to add a $scope.$watch on the specified scop variable. When the value of the variable changes the popover text will be updated with the change. |
 * | awRequiredWhen | Adds aw-required-when directive. Set to an object to be evaluated by the directive. |
 * | capitalize | true or false. If true, apply the 'capitalize' filter to the field. |
 * | class | String cotaining one or more CSS class values. |
 * | column | If the twoColumn option is being used, supply an integer value of 1 or 2 representing the column in which to place the field. 1 places the field in the left column, and 2 places it on the right. |
 * | dataContainer | Used with awPopOver. String providing the containment parameter. |
 * | dataPlacement | Used with awPopOver and awToolTip. String providing the placement parameter (i.e. left, right, top, bottom, etc.). |
 * | dataTitle | Used with awPopOver. String value for the title of the popover. |
 * | default | Default value to place in the field when the form is in 'add' mode. |
 * | defaultText | Default value to put into a select input. |
 * | falseValue | For radio buttons and checkboxes. Value to set the model to when the checkbox or radio button is not selected. |
 * | genHash | true or false. If true, places the field in an input group with a button that when clicked replaces the field contents with a hash as key. Used with host_config_key on the job templates detail page. |
 * | integer | Adds the integer directive to validate that the value entered is of type integer. Add min and max to supply lower and upper range bounds to the entered value. |
 * | label | Text to use as &lt;label&gt; element for the field |
 * | ngChange | Adds ng-change directive. Set to the JS expression to be evaluated by ng-change. |
 * | ngClick | Adds ng-click directive. Set to the JS expression to be evaluated by ng-click. |
 * | ngHide | Adds ng-hide directive. Set to the JS expression to be evaluated by ng-hide. |
 * | ngShow | Adds ng-show directive. Set to the JS expression to be evaluated by ng-show. |

 * | readonly | Defaults to false. When true the readonly attribute is set, disallowing changes to field content. |
 * | required | boolean. Adds required flag to form field |
 * | rows | Integer value used to set the row attribute for a textarea. |
 * | sourceModel | Used in conjunction with sourceField when the data for the field is part of the summary_fields object returned by the API. Set to the name of the summary_fields object that contains the field. For example, the job_templates object returned by the API contains summary_fields.inventory. |
 * | sourceField | String containing the summary_field.object.field name from the API summary_field object. For example, if a fields should be associated to the summary_fields.inventory.name, set the sourceModel to 'inventory' and the sourceField to 'name'. |
 * | spinner | true or false. If true, adds aw-spinner directive. Optionally add min and max attributes to control the range of allowed values. |
 * | type | String containing one of the following types defined in buildField: alertblock, hidden, text, password, email, textarea, select, number, checkbox, checkbox_group, radio, lookup, custom. |
 * | trueValue | For radio buttons and checkboxes. Value to set the model to when the checkbox or radio button is selected. |
 * | hasShowInputButton (sensitive type only) | This creates a button next to the input that toggles the input as text and password types. |
 * The form object contains a buttons object for defining any buttons to be included in the generated HTML. Generally all forms will have a Reset and a Submit button. If no buttons should be generated define buttons as an empty object, or set the showButtons option to false.
 *
 * The icon used for the button is determined by SelectIcon() found in js/shared/generator-helpers.js.
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | class | If the name of the button is reset or save, the class is automatically set to the correct bootstrap btn class for the color. Otherwise, provide a string with any classes to be added to the &lt;button&gt element. |
 * | label | For reset and save buttons the label is automatically set. For other types of buttons set label to the text string that should appear in the button. |
 * | ngClick | Adds the ng-click directive to the button. Set to the JS expression for the ng-click directive to evaluate. |
 * | ngDisabled | Only partially implemented at this point. For buttons other than reset, the ng-disabled directive is always added. The button will be disabled when the form is in an invalid state. |
 *
 * The form object may contain an actions object. The action object can contain one or more button definitions for buttons to appear in the top-right corner of the form. This may include activity stream, refresh, properties, etc. Each button object defined in actions may have the following attributes:
 *
 * | Attribute | Description |
 * | --------- | ----------- |
 * | awToolTip | Text or html to display in the button tooltip. Adds the aw-tool-tip directive. |
 * | class | Optional classes to add to the &lt;button&gt; element. |
 * | dataPlacement | Set the placement attribute of the tooltip - left, right, top, bottom, etc. |
 * | ngClick | Set to the JS expression to be evaluated by the ng-click directive. |
 * | mode | Set to edit or add, depending on which mode the button  |
 * |
 *
 * The form object may contain a related object. The related object contains one or more list objects defining sublists to display in accordions. For example, the Organization form contains a related users list and admins list.
 *
 * As originally conceived sublists were stored inside the form definition without regard to any list definitions found in the lists folder. In other words, lists/Users.js is completely different from the related.users object found in forms/Organizations.js. In reality they
 * are very similar and lists/Users.js should be used to generate the users sublist on the organizations detail page.
 *
 * One approach to making this work and using list definintion inside a from was implemented in forms/JobTemplates.js. In controllers/JobTemplates.js within JobTemplatesEdit() the form object is created by calling the JobTemplateForm() method found in forms/JobTemplates.js. The
 * method injects the SchedulesList and CompletedJobsList into the form object as related sets. Going forward this approach or similar should be used whenever a sublist needs to be added to a form.
 *
 * #Variable editing
 *
 * If the field type is textarea and the name is one of variables, extra_vars, inventory_variables or source_vars, then the parse type radio button group is added. This is the radio button group allowing the user to switch between JSON and YAML.
 *
 * Applying CodeMirror to the text area is handled by ParseTypeChange() found in helpers/Parse.js. Within the controller will be a call to ParseTypeChange that creates the CodeMirror object and sets up the required $scope methods for handles getting, setting and type conversion.
 */

import GeneratorHelpers from './generator-helpers';
import listGenerator from './list-generator/main';

export default
angular.module('FormGenerator', [GeneratorHelpers.name, 'Utilities', listGenerator.name])

.factory('GenerateForm', ['$rootScope', '$compile', 'generateList',
    'Attr', 'Icon', 'Column',
    'NavigationLink', 'Empty', 'SelectIcon',
    'ActionButton', 'MessageBar', '$log', 'i18n',
    function ($rootScope, $compile, GenerateList,
        Attr, Icon, Column, NavigationLink,
        Empty, SelectIcon, ActionButton, MessageBar, $log, i18n) {
        return {

            setForm: function (form) { this.form = form; },

            attr: Attr,

            icon: Icon,

            accordion_count: 0,

            scope: null,

            has: function (key) {
                return (this.form[key] && this.form[key] !== null && this.form[key] !== undefined) ? true : false;
            },
            // Not a very good way to do this
            // Form sub-states expect to target ui-views related@stateName & modal@stateName
            // Also wraps mess of generated HTML in a .card and at-Panel
            wrapPanel(html, ignorePanel){
                if(ignorePanel) {
                    return `
                    <div>
                    ${html}
                    <div ui-view="related"></div>
                    <div ui-view="modal"></div>
                    </div>`;
                }
                else {
                    return `
                    ${MessageBar(this.form)}
                    <div class="card at-Panel">
                    ${html}
                    <div ui-view="related"></div>
                    <div ui-view="modal"></div>
                    </div>`;
                }
            },

            inject: function (form, options) {
                //
                // Use to inject the form as html into the view.  View MUST have an ng-bind for 'htmlTemplate'.
                // Returns scope of form.
                //

                var element, fld, set, show, self = this;

                if (options.modal) {
                    if (options.modal_body_id) {
                        element = angular.element(document.getElementById(options.modal_body_id));
                    } else {
                        // use default dialog
                        element = angular.element(document.getElementById('form-modal-body'));
                    }
                } else {
                    if (options.id) {
                        element = angular.element(document.getElementById(options.id));
                    } else {
                        element = angular.element(document.getElementById('htmlTemplate'));
                    }
                }

                this.mode = options.mode;
                this.modal = (options.modal) ? true : false;
                this.setForm(form);

                if (options.html) {
                    element.html(options.html);
                } else {
                    element.html(this.build(options));
                }

                if (options.scope) {
                    this.scope = options.scope;
                } else {
                    this.scope = element.scope();
                }

                if (options.mode) {
                    this.scope.mode = options.mode;
                }

                if(options.mode === 'edit' && this.form.related &&
                    !_.isEmpty(this.form.related)){
                    var tabs = [this.form.name], that = this;
                    tabs.push(Object.keys(this.form.related));
                    tabs = _.flatten(tabs);
                    _.map(tabs, function(itm){
                        that.scope.$parent[itm+"Selected"] = false;
                    });
                    this.scope.$parent[this.form.name+"Selected"] = true;


                    this.scope.$parent.toggleFormTabs = function($event){
                        _.map(tabs, function(itm){
                            that.scope.$parent[itm+"Selected"] = false;
                        });
                        that.scope.$parent[$event.target.id.split('_tab')[0]+"Selected"] = true;
                    };

                }

                for (fld in form.fields) {
                    this.scope[fld + '_field'] = form.fields[fld];
                    this.scope[fld + '_field'].name = fld;
                }

                for (fld in form.headerFields){
                    this.scope[fld + '_field'] = form.headerFields[fld];
                    this.scope[fld + '_field'].name = fld;
                }

                $compile(element)(this.scope);

                if (!options.html) {
                    // Reset the scope to prevent displaying old data from our last visit to this form
                    for (fld in form.fields) {
                        this.scope[fld] = null;
                    }
                    for (set in form.related) {
                        this.scope[set] = null;
                    }
                    // if (((!options.modal) && options.related) || this.form.forceListeners) {
                    //     this.addListeners();
                    // }
                    if (options.mode === 'add') {
                        this.applyDefaults(form, this.scope);
                    }
                }

                // Remove any lingering tooltip and popover <div> elements
                $('.tooltip').each(function () {
                    $(this).remove();
                });

                $('.popover').each(function () {
                    // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                    $(this).remove();
                });

                try {
                    $('#help-modal').empty().dialog('destroy');
                } catch (e) {
                    //ignore any errors should the dialog not be initialized
                }

                if (options.modal) {
                    $rootScope.flashMessage = null;
                    this.scope.formModalActionDisabled = false;
                    this.scope.formModalInfo = false; //Disable info button for default modal
                    if (form) {
                        if (options.modal_title_id) {
                            this.scope[options.modal_title_id] = (options.mode === 'add') ? form.addTitle : form.editTitle;
                        } else {
                            this.scope.formModalHeader = (options.mode === 'add') ? form.addTitle : form.editTitle; //Default title for default modal
                        }
                    }
                    if (options.modal_selector) {
                        $(options.modal_selector).modal({
                            show: true,
                            backdrop: 'static',
                            keyboard: true
                        });
                        $(options.modal_selector).on('shown.bs.modal', function () {
                            $(options.modal_select + ' input:first').focus();
                        });
                        $(options.modal_selector).on('hidden.bs.modal', function () {
                            $('.tooltip').each(function () {
                                // Remove any lingering tooltip and popover <div> elements
                                $(this).remove();
                            });

                            $('.popover').each(function () {
                                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                                $(this).remove();
                            });
                        });
                    } else {
                        show = (options.show_modal === false) ? false : true;
                        $('#form-modal').modal({
                            show: show,
                            backdrop: 'static',
                            keyboard: true
                        });
                        $('#form-modal').on('shown.bs.modal', function () {
                            $('#form-modal input:first').focus();
                        });
                        $('#form-modal').on('hidden.bs.modal', function () {
                            $('.tooltip').each(function () {
                                // Remove any lingering tooltip and popover <div> elements
                                $(this).remove();
                            });

                            $('.popover').each(function () {
                                // remove lingering popover <div>. Seems to be a bug in TB3 RC1
                                $(this).remove();
                            });
                        });
                    }
                    $(document).bind('keydown', function (e) {
                        if (e.keyCode === 27) {
                            if (options.modal_selector) {
                                $(options.modal_selector).modal('hide');
                            }
                            $('#prompt-modal').modal('hide');
                            $('#form-modal').modal('hide');
                        }
                    });
                }

                if (self.scope && !self.scope.$$phase) {
                    setTimeout(function() {
                        if (self.scope) {
                            self.scope.$digest();
                        }
                    }, 100);
                }

                return self.scope;

            },

            buildHTML: function(form, options) {
                // Get HTML without actually injecting into DOM. Caller is responsible for any injection.
                // Example:
                //   html = GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });

                this.mode = options.mode;
                //this.modal = (options.modal) ? true : false;
                this.setForm(form);
                return this.build(options);
            },

            applyDefaults: function (form, scope, ignoreMode) {
                if(!ignoreMode) {
                    // Note: This is a hack. Ideally, mode should be set in each <resource>-<mode>.controller.js
                    // The mode is needed by the awlookup directive to auto-populate form fields when there is a
                    // single related resource.
                    scope.mode = this.mode;
                }

                for (var fld in form.fields) {
                    if (form.fields[fld]['default'] || form.fields[fld]['default'] === 0) {
                        if (form.fields[fld].type === 'select' && scope[fld + '_options']) {
                            scope[fld] = scope[fld + '_options'][form.fields[fld]['default']];
                        } else {
                            scope[fld] = form.fields[fld]['default'];
                        }
                    }
                }
            },

            reset: function () {
                // The form field values cannot be reset with jQuery. Each field is tied to a model, so to clear the field
                // value, you have to clear the model.

                var fld, scope = this.scope,
                    form = this.form;

                if (scope[form.name + '_form']) {
                    scope[form.name + '_form'].$setPristine();
                }

                function resetField(f, fld) {
                    // f is the field object, fld is the key

                    if (f.type === 'checkbox_group') {
                        for (var i = 0; i < f.fields.length; i++) {
                            scope[f.fields[i].name] = '';
                            scope[f.fields[i].name + '_api_error'] = '';
                            scope[form.name + '_form'][f.fields[i].name].$setValidity('apiError', true);
                        }
                    } else {
                        scope[fld] = '';
                        scope[fld + '_api_error'] = '';
                    }
                    if (f.sourceModel) {
                        scope[f.sourceModel + '_' + f.sourceField] = '';
                        scope[f.sourceModel + '_' + f.sourceField + '_api_error'] = '';
                        if (scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField]) {
                            scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setValidity('apiError', true);
                        }
                    }
                    if (f.type === 'lookup' && scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField]) {
                        scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setPristine();
                        scope[form.name + '_form'][f.sourceModel + '_' + f.sourceField].$setValidity('apiError', true);
                    }
                    if (scope[form.name + '_form'][fld]) {
                        scope[form.name + '_form'][fld].$setPristine();
                        scope[form.name + '_form'][fld].$setValidity('apiError', true);
                    }
                    if (f.awPassMatch && scope[form.name + '_form'][fld]) {
                        scope[form.name + '_form'][fld].$setValidity('awpassmatch', true);
                    }
                    if (f.subCheckbox) {
                        scope[f.subCheckbox.variable] = false;
                    }
                }

                for (fld in form.fields) {
                    resetField(form.fields[fld], fld);
                }
                if (form.statusFields) {
                    for (fld in form.statusFields) {
                        resetField(form.statusFields[fld], fld);
                    }
                }
                if (this.mode === 'add') {
                    this.applyDefaults(form, scope);
                }
            },

            checkAutoFill: function(params) {
                var fld, model, newVal, type,
                    scope = (params && params.scope) ? params.scope : this.scope;
                for (fld in this.form.fields) {
                    if (this.form.fields[fld].type === 'text' || this.form.fields[fld].type === 'textarea') {
                        type = (this.form.fields[fld].type === 'text') ? 'input' : 'textarea';
                        model = scope[this.form.name + '_form'][fld];
                        newVal = $(type + '[name="' + fld + '"]').val();
                        if (newVal && model && model.$viewValue !== newVal) {
                            model.$setViewValue(newVal);
                        }
                    }
                }
            },

            genID: function () {
                var id = new Date();
                return id.getTime();
            },

            headerField: function (fld, field) {
                var html = '';
                if (field.label) {
                    html += "<label>" + field.label + "</label>\n";
                }
                html += "<input type=\"text\" name=\"" + fld + "\" ";
                html += "ng-model=\"" + fld + "\" ";
                html += " readonly />\n";
                return html;
            },

            clearApiErrors: function (scope) {
                for (var fld in this.form.fields) {
                    if (this.form.fields[fld].sourceModel) {
                        scope[this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '_api_error'] = '';
                        $('[name="' + this.form.fields[fld].sourceModel + '_' + this.form.fields[fld].sourceField + '"]').removeClass('ng-invalid');
                    } else if (this.form.fields[fld].realName) {
                        this.scope[this.form.fields[fld].realName + '_api_error'] = '';
                        $('[name="' + this.form.fields[fld].realName + '"]').removeClass('ng-invalid');
                    } else {
                        scope[fld + '_api_error'] = '';
                        $('[name="' + fld + '"]').removeClass('ng-invalid');
                    }
                }
                if (!scope.$$phase) {
                    scope.$digest();
                }
            },

            navigationLink: NavigationLink,

            buildHeaderField: function(key, field, options, form){
                var html = '';
                // extend these blocks to include elements similarly buildField()
                if (field.type === 'toggle'){
                    html += `
                        <div class="Field-header--${key} ${field['class']} ${field.columnClass}">
                            <at-switch on-toggle="${field.ngClick}" switch-on="${"flag" in field} ? ${form.iterator}.${field.flag} : ${form.iterator}.enabled" switch-disabled="${"ngDisabled" in field} ? ${field.ngDisabled} : false" tooltip-string="${field.awToolTip}" tooltip-placement="${field.dataPlacement ? field.dataPlacement : 'right'}"></at-switch>
                        </div>
                    `;
                } else if (field.type === 'html') {
                    html += field.html;
                }
                return html;
            },


            buildField: function (fld, field, options, form) {
                var i, fldWidth, offset, html = '', error_message,
                    horizontal = (this.form.horizontal) ? true : false;

                function getFieldWidth() {
                    var x;
                    if (form.formFieldSize) {
                        x = form.formFieldSize;
                    } else if (field.xtraWide) {
                        x = "col-lg-10";
                    } else if (field.column) {
                        x = "col-lg-8";
                    } else if (!form.formFieldSize && options.modal) {
                        x = "col-lg-10";
                    } else {
                        x = "col-lg-6";
                    }
                    return x;
                }

                function getLabelWidth() {
                    var x;
                    if (form.formLabelSize) {
                        x = form.formLabelSize;
                    } else if (field.column) {
                        x = "col-lg-4";
                    } else if (!form.formLabelSize && options.modal) {
                        x = "col-lg-2";
                    } else {
                        x = "col-lg-2";
                    }
                    return x;
                }

                function buildId(field, fld, form) {
                    var html = '';
                    if (field.id) {
                        html += Attr(field, 'id');
                    } else {
                        html += "id=\"" + form.name + "_" + fld + "\" ";
                    }
                    return html;
                }

                function buildCheckbox(form, field, fld, idx) {
                    var html = '';

                    html += "<div class=\"form-check\" ";
                    html += (field.ngShow) ? " ng-show=\"" +field.ngShow + "\" " : "";
                    html += ">";
                    html += "<label class=\"form-check-label\">";
                    html += "<input type=\"checkbox\" ";
                    html += Attr(field, 'type');
                    html += "ng-model=\"" + fld + '" ';
                    html += "name=\"" + fld + '" ';
                    html += (field.ngChange) ? Attr(field, 'ngChange') : "";
                    html += "id=\"" + form.name + "_" + fld + "_chbox";
                    html += (idx !== undefined) ? "_" + idx : "";
                    html += "\" class=\"form-check-input\"";
                    html += (field.trueValue !== undefined) ? Attr(field, 'trueValue') : "";
                    html += (field.falseValue !== undefined) ? Attr(field, 'falseValue') : "";
                    html += (field.checked) ? "checked " : "";
                    html += (field.readonly) ? "disabled " : "";
                    html += (field.ngChange) ? "ng-change=\"" +field.ngChange + "\" " : "";
                    html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                    html += `/><span class="Form-inputLabel">${field.label}</span></label>`;
                    html += (field.awPopOver) ? Attr(field, 'awPopOver', fld) : "";
                    html += `</div>`;

                    return html;
                }

                function label(options) {
                    var html = '';
                    if (field.label || field.labelBind) {
                        html += "<label class=\"";
                        html += (field.labelClass) ? field.labelClass : "";
                        html += (horizontal) ? " " + getLabelWidth() : "Form-inputLabelContainer ";
                        html += (field.showParseTypeToggle) ? "Form-inputLabelContainer--codeMirror " : "";
                        html += "\" ";
                        html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
                        html += "for=\"" + fld + '">\n';

                        html += `${field.required ? '<span class="Form-requiredAsterisk">*</span>' : ''}`;

                        html += (field.icon) ? Icon(field.icon) : "";
                        if (field.labelBind) {
                            html += "\t\t<span class=\"Form-inputLabel\" ng-bind=\"" + field.labelBind + "\" translate>\n\t\t</span>";
                        } else {
                            html += "\t\t<span class=\"Form-inputLabel\" translate>\n\t\t\t" + field.label + "\n\t\t</span>";
                        }
                        html += ((field.awPopOver || field.awPopOverWatch) && !field.awPopOverRight) ? Attr(field, 'awPopOver', fld) : "";
                        html += (field.hintText) ? "\n\t\t<span class=\"label-hint-text\">\n\t\t\t<i class=\"fa fa-info-circle\">\n\t\t\t</i>\n\t\t\tHint: " + field.hintText + "\n\t\t</span>" : "";
                        // Variable editing
                        if (fld === "variables" || fld === "extra_vars" || _.last(fld.split('_')) === 'variables' || fld === 'source_vars' || field.showParseTypeToggle === true) {
                            let parseTypeId = `${form.name}_${fld}_parse_type`;
                            let parseTypeName = field.parseTypeName || 'parseType';
                            let getToggleClass = (primary, secondary) => `{
                                'btn-primary': ${parseTypeName} === '${primary}',
                                'Button-primary--hollow' : ${parseTypeName} === '${secondary}'
                            }`;
                            let toggleLeftClass = getToggleClass('yaml', 'json');
                            let toggleRightClass = getToggleClass('json', 'yaml');

                            html += `
                                <div class="FormToggle-container" id="${parseTypeId}">
                                    <div class="btn-group">
                                        <label ng-class="${toggleLeftClass}" class="btn btn-xs">
                                            <input type="radio" value="yaml" ng-model="${parseTypeName}" ng-change="parseTypeChange('${parseTypeName}', '${fld}')" />YAML
                                        </label>
                                        <label ng-class="${toggleRightClass}" class="btn btn-xs">
                                            <input type="radio" value="json" ng-model="${parseTypeName}" ng-change="parseTypeChange('${parseTypeName}', '${fld}')" />JSON
                                        </label>
                                    </div>
                                </div>`;
                        }

                        if (options && options.checkbox) {
                            html += createCheckbox(options.checkbox);
                        }

                        if (field.labelAction) {
                            let action = field.labelAction;
                            let href = action.href || "";
                            let ngClick = action.ngClick || "";
                            let cls = action["class"] || "";
                            html += `<a class="Form-labelAction ${cls}" href="${href}" ng-click="${ngClick}">${action.label}</a>`;
                        }

                        if(field.reset && !field.disabled) {
                            var resetValue = "'" + field.reset+ "'";
                            var resetMessage = i18n._('Revert');
                            html+= `<a class="Form-resetValue" ng-click="resetValue(${resetValue})">${resetMessage}</a>`;
                        }

                        html += "\n\t</label>\n";
                    }

                    return html;
                }

                if (field.type === 'toggle'){
                    html += `
                        <td class="List-tableCell-${fld}-column ${field['class']} ${field.columnClass}">
                            <at-switch on-toggle="${field.ngClick}" switch-on="${"flag" in field} ? ${form.iterator}.${field.flag} : ${form.iterator}.enabled" switch-disabled="${"ngDisabled" in field} ? ${field.ngDisabled} : false" tooltip-string="${field.awToolTip}" tooltip-placement="${field.dataPlacement ? field.dataPlacement : 'right'}"></at-switch>
                        </td>
                    `;
                }

                if (field.type === 'alertblock') {
                    html += "<div class=\"row\">\n";
                    html += "<div class=\"";
                    html += (options.modal || options.id) ? "col-lg-12" : "col-lg-12";
                    html += "\">\n";
                    html += "<div class=\"Form-alertblock";
                    html += (field.closeable === undefined || field.closeable === true) ? " alert-dismissable" : "";
                    html += "\" ";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += ">\n";
                    html += (field.closeable === undefined || field.closeable === true) ?
                        "<button aria-label=\"{{'Close'|translate}}\" type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-hidden=\"true\">&times;</button>\n" : "";
                    html += field.alertTxt;
                    html += "</div>\n";
                    html += "</div>\n";
                    html += "</div>\n";
                }

                if ((!field.readonly) || (field.readonly && options.mode === 'edit')) {

                    if((field.excludeMode === undefined || field.excludeMode !== options.mode) && field.type !== 'alertblock' && field.type !== 'workflow-chart') {

                    html += `<div id='${form.name}_${fld}_group' class='form-group Form-formGroup `;
                    html += (field.disabled) ? `Form-formGroup--disabled ` : ``;
                    html += (field.type === "checkbox") ? "Form-formGroup--checkbox " : "";
                    html += (field['class']) ? (field['class']) : "";
                    html += "'";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += (field.ngHide) ? this.attr(field, 'ngHide') : "";
                    html += ">\n";

                    var definedInFileMessage = i18n._('This setting has been set manually in a settings file and is now disabled.');
                    html += (field.definedInFile) ?
                        `<span class="Form-tooltip--disabled">${definedInFileMessage}</span>` : ``;

                    // toggle switches
                    if(field.type === 'toggleSwitch') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngModel: field.subCheckbox.variable,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);

                        html += `
                            <div>
                                <at-switch on-toggle="toggleForm('${field.toggleSource}')" switch-on="${field.toggleSource}" switch-disabled="${"ngDisabled" in field} ? ${field.ngDisabled} : false" hide="!(${"ngShow" in field ? field.ngShow : true})"></at-switch>
                                <div class="error api-error" id="${this.form.name}-${fld}-api-error" ng-bind="${fld}_api_error"></div>
                            </div>
                        `;
                    }

                    //text fields
                    if (field.type === 'text' || field.type === 'password' || field.type === 'email') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngModel: field.subCheckbox.variable,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += (field.clear || field.genHash) ? "<div class=\"input-group Form-mixedInputGroup\">\n" : "";

                        if (field.control === null || field.control === undefined || field.control) {
                            html += "<input ";
                            html += this.attr(field, 'type');
                            html += "ng-model=\"" + fld + '" ';
                            html += 'name="' + fld + '" ';
                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += buildId(field, fld, this.form);
                            html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : "";
                            html += "class=\"form-control Form-textInput";
                            html += "\" ";
                            html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                            html += (field.required) ? "required " : "";
                            html += (field.disabled) ? `disabled="disabled" `: ``;
                            html += (field.readonly || field.showonly) ? "readonly " : "";
                            html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                            html += (field.capitalize) ? "capitalize " : "";
                            html += (field.awSurveyQuestion) ? "aw-survey-question" : "" ;
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                            if(field.awRequiredWhen) {
                                html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                                html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                                html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                            }
                            html += (field.awValidUrl) ? "aw-valid-url " : "";
                            html += "/>\n";
                        }

                        if (field.clear) {
                            html += "<span class=\"input-group-btn\"><button aria-label=\"{{'Clear field'|translate}}\" type=\"button\" ";
                            html += "id=\"" + this.form.name + "_" + fld + "_clear_btn\" ";
                            html += "class=\"btn btn-default\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " +
                                "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\" ";
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += " ><i class=\"fa fa-undo\"></i></button>\n";
                            html += "</span>\n</div>\n";
                        }

                        if (field.genHash) {
                            const defaultGenHashButtonTemplate = `
                                <span class="input-group-btn input-group-prepend">
                                    <button
                                        aria-label="{{'Generate field'|translate}}"
                                        type="button"
                                        class="btn Form-lookupButton"
                                        ng-click="genHash('${fld}')"
                                        aw-tool-tip="Generate ${field.label}"
                                        data-placement="top"
                                        id="${this.form.name}_${fld}_gen_btn"
                                    >
                                        <i class="fa fa-refresh"></i>
                                    </button>
                                </span>`;
                            const genHashButtonTemplate = _.get(field, 'genHashButtonTemplate', defaultGenHashButtonTemplate);
                            html += `${genHashButtonTemplate}\n</div>\n`;
                        }

                        // Add error messages
                        if (field.required || field.awRequiredWhen) {
                            error_message = i18n._('Please enter a value.');
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : error_message) + "</div>\n";
                        }
                        if (field.type === "email") {
                            error_message = i18n._('Please enter a valid email address.');
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-email-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + `.$error.email">${error_message}</div>`;
                        }
                        if (field.awPassMatch) {
                            error_message = i18n._('This value does not match the password you entered previously.  Please confirm that password.');
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-passmatch-error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                `.$error.awpassmatch">${error_message}</div>`;
                        }
                        if (field.awValidUrl) {
                            error_message = i18n._("Please enter a URL that begins with ssh, http or https.  The URL may not contain the '@' character.");
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-url-error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                `.$error.awvalidurl">${error_message}</div>`;
                        }

                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

                        html += "</div>\n";
                    }

                    //fields with sensitive data that needs to be obfuscated from view
                    if (field.type === 'sensitive') {
                        field.showInputInnerHTML = i18n._("Show");
                        field.inputType = "password";

                        html += "\t" + label();
                        if (field.hasShowInputButton) {
                            var tooltip = i18n._("Toggle the display of plaintext.");
                            html += "\<div class='input-group Form-mixedInputGroup";
                            html += (horizontal) ? " " + getFieldWidth() : "";
                            html += "'>\n";
                            // TODO: make it so that the button won't show up if the mode is edit, hasShowInputButton !== true, and there are no contents in the field.
                            html += "<span class='input-group-btn input-group-prepend'>\n";
                            html += "<button aw-password-toggle type='button' class='btn btn-default show_input_button Form-passwordButton' ";
                            html += buildId(field, fld + "_show_input_button", this.form);
                            html += `aw-tool-tip='${tooltip}'} aw-tip-placement='top'`;
                            html += "tabindex='-1' ";
                            html += (field.ngDisabled) ? "ng-disabled='" + field.ngDisabled + "'" : "";
                            html += ">\n" + field.showInputInnerHTML;
                            html += "\n</button>\n";
                            html += "</span>\n";
                        } else {
                            html += "<div";
                            html += (horizontal) ? " class='" + getFieldWidth() + "'" : "";
                            html += ">\n";
                        }

                        if (field.control === null || field.control === undefined || field.control) {
                            html += "<input ";
                            html += (field.disabled) ? `disabled="disabled" `: ``;
                            html += buildId(field, fld + "_input", this.form);
                            html += "type='password' ";
                            html += "ng-model=\"" + fld + '" ';
                            html += 'name="' + fld + '" ';

                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += buildId(field, fld, this.form);

                            html += (field.controlNGClass) ? "ng-class='" + field.controlNGClass + "' " : "";
                            html += "class='form-control Form-textInput";
                            html += "' ";

                            html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                            html += (field.required) ? "required " : "";
                            html += (field.ngRequired) ? `ng-required="${field.ngRequired}"` : "";
                            html += (field.readonly || field.showonly) ? "readonly " : "";

                            html += (field.awPassMatch) ? "awpassmatch='" + field.associated + "' " : "";
                            html += (field.capitalize) ? "capitalize " : "";
                            html += (field.awSurveyQuestion) ? "aw-survey-question" : "";

                            html += (field.ngDisabled) ? "ng-disabled='" + field.ngDisabled + "'" : "";

                            html += (field.autocomplete !== undefined) ? this.attr(field, 'autocomplete') : "";
                            if(field.awRequiredWhen) {
                                html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                                html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                                html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                            }
                            html += (field.awValidUrl) ? "aw-valid-url " : "";
                            html += "/>\n";
                        }

                        html += "</div>\n";

                        // Add error messages
                        if (field.required || field.awRequiredWhen) {
                            error_message = i18n._("Please enter a value.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-required-error' ng-show='" + this.form.name + "_form." + fld + ".$dirty && " +
                                this.form.name + "_form." + fld + ".$error.required'>\n" + (field.requiredErrorMsg ? field.requiredErrorMsg : error_message) + "\n</div>\n";
                        }
                        if (field.type === "email") {
                            error_message = i18n._("Please enter a valid email address.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-email-error' ng-show='" + this.form.name + "_form." + fld + ".$dirty && " +
                                this.form.name + "_form." + fld + `.$error.email'>${error_message}</div>`;
                        }
                        if (field.awPassMatch) {
                            error_message = i18n._("This value does not match the password you entered previously.  Please confirm that password.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-passmatch-error' ng-show='" + this.form.name + "_form." + fld +
                                `.$error.awpassmatch'>${error_message}</div>`;
                        }
                        if (field.awValidUrl) {
                            error_message = i18n._("Please enter a URL that begins with ssh, http or https.  The URL may not contain the '@' character.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-url-error' ng-show='" + this.form.name + "_form." + fld +
                                `.$error.awvalidurl'>${error_message}</div>`;
                        }

                        html += "<div class='error api-error' id='" + this.form.name + "-" + fld + "-api-error' ng-bind='" + fld + "_api_error'>\n</div>\n";
                    }

                    //textarea fields
                    if (field.type === 'textarea') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngModel: field.subCheckbox.variable,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<textarea ";
                        html += (field.disabled) ? `disabled="disabled" `: ``;
                        html += (field.rows) ? this.attr(field, 'rows') : "";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += "class=\"form-control Form-textArea";
                        html += (field.class) ? " " + field.class : "";
                        html += (field.elementClass) ? " " + field.elementClass : "";
                        html += "\" ";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += buildId(field, fld, this.form);
                        html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                        html += (field.ngDisabled) ? this.attr(field, 'ngDisabled'): "";
                        html += (field.required) ? "required " : "";
                        html += (field.ngRequired) ? "ng-required=\"" + field.ngRequired +"\"" : "";
                        html += (field.ngTrim !== undefined) ? "ng-trim=\"" + field.ngTrim +"\"" : "";
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        html += (field.awDropFile) ? "aw-drop-file " : "";
                        if(field.awRequiredWhen) {
                            html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                            html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                            html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                        }
                        html += "aw-watch ></textarea>\n";

                        // Add error messages
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : i18n._("Please enter a value.")) + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //select field
                    if (field.type === 'select') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngShow: field.subCheckbox.ngShow,
                                ngModel: field.subCheckbox.variable,
                                ngChange: field.subCheckbox.ngChange,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text
                            };
                        }

                        if (field.onError) {
                            labelOptions.onError = {
                                id: `${this.form.name}_${fld}_error_text`,
                                ngShow: field.onError.ngShow,
                                ngModel: field.onError.variable,
                                text: field.onError.text
                            };
                        }

                        html += label(labelOptions);

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<div class=\"Form-dropDownContainer\">\n";
                        html += "<select ";
                        html += (field.disabled) ? `disabled="disabled" `: ``;
                        html += "ng-model=\"" + (field.ngModel ? field.ngModel : fld) + '" ';
                        html += 'name="' + fld + '" ';
                        html += "class=\"form-control Form-dropDown";
                        html += "\" ";
                        html += (field.ngOptions) ? this.attr(field, 'ngOptions') : "" ;
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.ngDisabled) ? this.attr(field, 'ngDisabled'): "";
                        html += (field.ngRequired) ? this.attr(field, 'ngRequired') : "";
                        html += (field.ngInit) ? this.attr(field, 'ngInit') : "";
                        html += buildId(field, fld, this.form);
                        html += (field.required) ? "required " : "";
                        //used for select2 combo boxes
                        html += (field.multiSelect) ? "multiple " : "";
                        html += (field.readonly) ? "disabled " : "";
                        if(field.awRequiredWhen) {
                            html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                            html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                            html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                        }
                        html += ">\n";
                        if(!field.multiSelect && !field.disableChooseOption){
                            html += "<option value=\"\">";
                            // some languages use "Playbook" as a proper noun
                            var chosen_item = (i18n._("playbook") !== i18n._("Playbook")) ? field.label.toLowerCase() : field.label;
                            // Add a custom default select 'value' (default text)
                            html += (field.defaultText) ? field.defaultText : i18n.sprintf(i18n._("Choose a %s"), chosen_item);
                            html += "</option>\n";
                        }

                        html += "</select>\n";
                        html += "</div>\n";

                            // Add error messages
                        if (field.required || field.awRequiredWhen) {
                                html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                    this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : i18n._("Please select a value."));
                                if (field.includePlaybookNotFoundError) {
                                    html += "  <span ng-show=\"playbookNotFound\">Playbook {{ job_template_obj.playbook }} not found for project.</span>\n";
                                }
                                html += "</div>\n";
                        }
                        if (field.label === "Labels") {
                            html += `<div class="error" id="${field.onError.id}" ng-show="${field.onError.ngShow}">${field.onError.text}</div>`;
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";


                        html += "</div>\n";
                    }

                    //number field
                    if (field.type === 'number') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngModel: field.subCheckbox.variable,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<input ";
                        html += (field.spinner) ? "" : "type=\"text\" ";
                        html += " value=\"" + field['default'] + "\" ";
                        html += "class=\"";
                        if (!field.slider && !field.spinner) {
                            html += "form-control";
                        }
                        html += "\" ";
                        html += (field.slider) ? "aw-slider=\"" + fld + "\" " : "";
                        html += (field.spinner) ? "aw-spinner=\"" + fld + "\" " : "";
                        html += "ng-model=\"" + fld + '" ';
                        html += 'name="' + fld + '" ';
                        html += buildId(field, fld, this.form);
                        html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                        html += (field.min || field.min === 0) ? this.attr(field, 'min') : "";
                        html += (field.max) ? this.attr(field, 'max') : "";
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                        html += (field.slider) ? "id=\"" + fld + "-number\"" : (field.id) ? this.attr(field, 'id') : "";
                        html += (field.required) ? "required " : "";
                        html += (field.readonly) ? "readonly " : "";
                        html += (field.integer) ? "integer " : "";
                        html += (field.disabled) ? "data-disabled=\"true\" " : "";
                        if(field.awRequiredWhen) {
                            html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                            html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                            html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                        }
                        html += " />\n";

                        // Add error messages
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : i18n._("Please select a value.")) + "</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">" + i18n._("Please enter a number.") + "</div>\n";
                        }
                        if (field.min !== undefined || field.max !== undefined) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">";
                            if (field.max !== undefined) {
                                html += i18n.sprintf(i18n._("Please enter a number greater than %d and less than %d."), field.min, field.max);
                            } else {
                                html += i18n.sprintf(i18n._("Please enter a number greater than %d."), field.min);
                            }
                            html += "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //checkbox group
                    if (field.type === 'checkbox_group') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<div class=\"checkbox-group\" ";
                        html += "id=\"" + this.form.name + "_" + fld + "_chbox_group\" ";
                        html += ">\n";
                        for (i = 0; i < field.fields.length; i++) {
                            html += buildCheckbox(this.form, field.fields[i], field.fields[i].name, i);
                        }
                        // Add error messages
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : i18n._("Please select at least one value.")) + "</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">" + i18n._("Please select a number.") + "</div>\n";
                        }
                        if (field.min || field.max) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">" + i18n._("Please select a number between ") + field.min + i18n._(" and ") +
                                field.max + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        for (i = 0; i < field.fields.length; i++) {
                            html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + field.fields[i].name + "-api-error\" ng-bind=\"" + field.fields[i].name + "_api_error\"></div>\n";
                        }
                        html += "</div><!-- checkbox-group -->\n";
                        html += "</div>\n";
                    }

                    //checkbox
                    if (field.type === 'checkbox') {

                        if (horizontal) {
                            fldWidth = getFieldWidth();
                            offset = 12 - parseInt(fldWidth.replace(/[A-Z,a-z,-]/g, ''),10);
                            html += "<div class=\"" + fldWidth + " col-lg-offset-" + offset + "\">\n";
                        }

                        html += "<div class=\"checkbox\">\n";
                        html += buildCheckbox(this.form, field, fld, undefined, false);
                        html += (field.icon) ? Icon(field.icon) : "";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";
                        html += "</div><!-- checkbox -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }
                    }

                    // radio button
                    if (field.type === 'radio') {

                        if (horizontal) {
                            fldWidth = getFieldWidth();
                            offset = 12 - parseInt(fldWidth.replace(/[A-Z,a-z,-]/g, ''),10);
                            html += "<div class=\"" + fldWidth + " col-lg-offset-" + offset + "\">\n";
                        }

                        html += "<div class=\"radio\">\n";
                        html += "<label ";
                        html += (field.labelBind) ? "ng-bind=\"" + field.labelBind + "\" " : "";
                        html += "for=\"" + fld + '">';

                        html += "<input type=\"radio\" ";
                        html += "name=\"" + fld + "\" ";
                        html += "value=\"" + field.value + "\" ";
                        html += "ng-model=\"" + field.ngModel + "\" ";
                        html += (field.ngChange) ? Attr(field, 'ngChange') : "";
                        html += (field.readonly) ? "disabled " : "";
                        html += (field.ngDisabled) ? Attr(field, 'ngDisabled') : "";
                        html += " /> ";
                        html += field.label;
                        html += "</label>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";
                        html += "</div><!-- radio -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }
                    }

                    //lookup type fields
                    if (field.type === 'lookup') {
                        let defaultLookupNgClick = `$state.go($state.current.name + '.${field.sourceModel}', {selected: ${field.sourceModel}})`;
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngModel: field.subCheckbox.variable,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += `<div class="input-group Form-mixedInputGroup">`;
                        html += "<span class=\"input-group-btn input-group-prepend\">\n";
                        html += `<button aria-label="{{'Lookup field'|translate}}" type="button" class="Form-lookupButton btn" ng-click="${field.ngClick || defaultLookupNgClick}"
                        ${field.readonly || field.showonly}
                        ${this.attr(field, "ngDisabled")}
                        id="${fld}-lookup-btn"><i class="fa fa-search"></i></button>`;
                        html += "</span>\n";
                        html += "<input type=\"text\" class=\"form-control Form-textInput input-medium lookup\" ";
                        html += "ng-model=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "name=\"" + field.sourceModel + '_' + field.sourceField + "\" ";
                        html += "class=\"form-control\" ";
                        html += (field.required) ? 'required ' : '';
                        html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                        html += (field.ngDisabled) ? this.attr(field, 'ngDisabled') : "" ;
                        html += (field.ngRequired) ? this.attr(field, 'ngRequired') : "";
                        html += (field.id) ? this.attr(field, 'id') : "";
                        html += (field.placeholder) ? this.attr(field, 'placeholder') : "";
                        html += (options.mode === 'edit' && field.editRequired) ? "required " : "";
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        if(field.awRequiredWhen) {
                            html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                            html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                            html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                        }
                        // the awlookup directive depends on a data-url attribute to make requests and set field validity
                        html += `data-basePath="${field.basePath}"`;
                        html += `data-source="${field.sourceModel}"`;
                        html += `data-query="?${field.sourceField}__iexact=:value"`;
                        html += (field.awLookupType !== undefined)  ? ` data-awLookupType=${field.awLookupType} ` : "";
                        html += (field.autopopulateLookup !== undefined)  ? ` autopopulateLookup=${field.autopopulateLookup} ` : "";
                        html += (field.watchBasePath !== undefined) ? ` watchBasePath=${field.watchBasePath} ` : "";
                        html += `ng-model-options="{ updateOn: 'default blur', debounce: { 'default': 300, 'blur': 0 } }"`;
                        html += (field.awLookupWhen !== undefined) ? this.attr(field, 'awLookupWhen') : "";
                        html += " awlookup />\n";
                        html += "</div>\n";

                        // Add error messages
                        if (field.required || field.awRequiredWhen) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" +
                                this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : i18n._("Please select a value.")) + "</div>\n";
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-notfound-error\" ng-show=\"" +
                                this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.awlookup && !(" + this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.required)\">" + i18n._("That value was not found.  Please enter or select a valid value.") + "</div>\n";
                        } else {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-notfound-error\" ng-show=\"" +
                                this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.awlookup\">" + i18n._("That value was not found.  Please enter or select a valid value.") + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField +
                            "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    if (field.type === 'code_mirror') {
                        html += '<at-code-mirror ';
                        html += `id="${form.name}_${fld}" `;
                        html += `class="${field.class}" `;
                        html += `label="${field.label}" `;
                        html += `tooltip="${field.awPopOver}" `;
                        html += `name="${fld}" `;
                        html += `variables="${field.variables}" `;
                        html += `ng-disabled="${field.ngDisabled}" `;
                        html += '></at-code-mirror>';
                    }

                    if (field.type === 'syntax_highlight') {
                        html += '<at-syntax-highlight ';
                        html += `id="${form.name}_${fld}" `;
                        html += `class="${field.class}" `;
                        html += `label="${field.label}" `;
                        html += `tooltip="${field.awPopOver || ''}" `;
                        html += `name="${fld}" `;
                        html += `value="${fld}" `;
                        html += `default="${field.default || ''}" `;
                        html += `rows="${field.rows || 6}" `;
                        html += `one-line="${field.oneLine || ''}"`;
                        html += `mode="${field.mode}" `;
                        html += `ng-disabled="${field.ngDisabled}" `;
                        html += '></at-syntax-highlight>';
                    }

                    if (field.type === 'custom') {
                        let labelOptions = {};

                        if (field.subCheckbox) {
                            labelOptions.checkbox = {
                                id: `${this.form.name}_${fld}_ask_chbox`,
                                ngShow: field.subCheckbox.ngShow,
                                ngChange: field.subCheckbox.ngChange,
                                ngModel: field.subCheckbox.variable,
                                ngDisabled: field.subCheckbox.ngDisabled || field.ngDisabled,
                                text: field.subCheckbox.text || ''
                            };
                        }

                        html += label(labelOptions);
                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";
                        html += "<div ";
                        html += "id=\"" + form.name + "_" + fld + "\" ";
                        html += (field.controlNGClass) ? "ng-class=\"" + field.controlNGClass + "\" " : "";
                        html += ">\n";
                        html += field.control;
                        html += "</div>\n";
                        html += "</div>\n";
                    }
                    html += "</div>\n";
                }
                }
                return html;
            },

            build: function (options) {
                //
                // Generate HTML. Do NOT call this function directly. Called by inject(). Returns an HTML
                // string to be injected into the current view.
                //
                var btn, button, fld, field, html = '', section, group,
                    sectionShow, offset, width,ngDisabled, itm;

                // title and exit button
                if(!(this.form.showHeader !== undefined && this.form.showHeader === false)) {
                    html +=  "<div class=\"Form-header\">";
                    html += "<div class=\"Form-title\">";
                    html += (options.mode === 'edit') ? this.form.editTitle : this.form.addTitle;
                    if(this.form.name === "user"){
                        html+= "<span class=\"Form-title--is_superuser\" "+
                            "ng-show='is_superuser'>" + i18n._("Admin") + "</span>";
                        html+= "<span class=\"Form-title--is_system_auditor\" "+
                            "ng-show='is_system_auditor'>" + i18n._("Auditor") + "</span>";
                        html+= "<span class=\"Form-title--is_ldap_user\" "+
                            "ng-show='ldap_user'>LDAP</span>";
                        html+= "<span class=\"Form-title--is_external_account\" "+
                            "ng-show='external_account'>{{external_account}}</span>";
                        html+= "<span class=\"Form-title--last_login\" "+
                            "ng-show='last_login'>" + i18n._("Last logged in: ") + "{{ last_login | longDate }}</span>";
                    }
                    if(this.form.name === "smartinventory"){
                        html+= "<span class=\"Form-title--is_smartinventory\" "+
                            ">" + i18n._("Smart Inventory") + "</span>";
                    }
                    html += "</div>\n";
                    html += "<div class=\"Form-header--fields\">";
                    if(this.form.headerFields){
                        var that = this;
                        _.forEach(this.form.headerFields, function(value, key){
                            html += that.buildHeaderField(key, value, options, that.form);
                        });
                        html += "</div>\n";
                    }
                    else{ html += "</div>\n"; }
                    if(this.form.cancelButton !== undefined && this.form.cancelButton === false) {
                        html += "<div class=\"Form-exitHolder\">";
                        html += "</div></div>";
                    } else {
                        html += "<div class=\"Form-exitHolder\">";
                        html += "<button aria-label=\"{{'Close'|translate}}\" class=\"Form-exit\" ng-click=\"formCancel()\">";
                        html += "<i class=\"fa fa-times-circle\"></i>";
                        html += "</button></div>\n";
                    }
                        html += "</div>"; //end of Form-header
                }

                if (!_.isEmpty(this.form.related) || !_.isEmpty(this.form.relatedButtons)) {
                    var collection, details = i18n._('Details');
                    html += "<div class=\"Form-tabHolder\">";

                    if(this.mode === "edit"){
                        html += `<div id="${this.form.name}_tab" class="Form-tab" `;
                        html += this.form.detailsClick ? `ng-click="` + this.form.detailsClick + `" ` : `ng-click="$state.go('${this.form.stateTree}.edit')" `;
                        let detailsTabSelected = this.form.activeEditState ? `$state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.$current.data.formChildState` : `$state.is('${this.form.stateTree}.edit') || $state.$current.data.formChildState`;
                        html += `ng-class="{'is-selected': ${detailsTabSelected} }" translate>` +
                            `${details}</div>`;

                        for (itm in this.form.related) {
                            collection = this.form.related[itm];
                            html += `<div id="${itm}_tab" `+
                                `class="Form-tab" `;
                            html += (this.form.related[itm].ngIf) ? ` ng-if="${this.form.related[itm].ngIf}" ` :  "";
                            html += (this.form.related[itm].ngClick) ? `ng-click="` + this.form.related[itm].ngClick + `" ` : `ng-click="$state.go('${this.form.stateTree}.edit.${itm}')" `;
                            if (collection.awToolTip && collection.awToolTipTabEnabledInEditMode === true) {
                                html += `aw-tool-tip="${collection.awToolTip}" ` +
                                `aw-tip-placement="${collection.dataPlacement}" ` +
                                `data-tip-watch="${collection.dataTipWatch}" `;
                            }
                            let relatedTabSelected;
                            if (this.form.related[itm].tabSelected) {
                                relatedTabSelected = this.form.related[itm].tabSelected;
                            } else {
                                relatedTabSelected = this.form.activeEditState ? `$state.includes('${this.form.activeEditState}.${itm}') || $state.includes('${this.form.stateTree}.edit.${itm}')` : `$state.includes('${this.form.stateTree}.edit.${itm}')`;
                            }

                            html += `ng-class="{'is-selected' : ${relatedTabSelected}` ;
                            if(this.form.related[itm].disabled){
                                html += `, 'Form-tab--disabled' : ${this.form.related[itm].disabled }`;
                            }
                            html +=  `}" translate>${(collection.title || collection.editTitle)}</div>`;
                        }

                        for (itm in this.form.relatedButtons) {
                            button = this.form.relatedButtons[itm];

                            // Build button HTML
                            html += "<button type=\"button\" ";
                            html += "class=\"btn btn-sm";
                            html += (button['class']) ? " " + button['class'] : "";
                            html += "\" ";
                            html += "id=\"" + this.form.name + "_" + itm + "_btn\" ";

                            if(button.ngShow){
                                html += this.attr(button, 'ngShow');
                            }
                            if (button.ngClick) {
                                html += this.attr(button, 'ngClick');
                            }
                            if (button.ngDisabled) {
                                ngDisabled = (button.ngDisabled===true) ? this.form.name+"_form.$invalid" : button.ngDisabled;
                                if (itm !== 'reset') {
                                    //html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid";
                                    html += "ng-disabled=\"" + ngDisabled;
                                    //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                    html += "\" ";
                                } else {
                                    //html += "ng-disabled=\"" + this.form.name + "_form.$pristine";
                                    //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                    //html += "\" ";
                                }
                            }
                            if(button.awToolTip) {
                                html += " aw-tool-tip='" + button.awToolTip + "' data-placement='" + button.dataPlacement + "' data-tip-watch='" + button.dataTipWatch + "'";
                            }
                            html += ">";
                            html += " " + button.label + "</button>\n";
                        }
                    }
                    else if(this.mode === "add"){
                        html += "<div id=\"" + this.form.name + "_tab\""+
                            `class="Form-tab is-selected">${details}</div>`;

                        for (itm in this.form.related) {
                            collection = this.form.related[itm];
                            html += "<div id=\"" + itm + "_tab\" ";
                            html += (this.form.related[itm].ngIf) ? ` ng-if="${this.form.related[itm].ngIf}" ` :  "";
                            html += collection.awToolTip ? "aw-tool-tip=\"" + collection.awToolTip + "\" aw-tip-placement=\"" + collection.dataPlacement + "\" " : "";
                            html += "data-container=\"body\" tooltipinnerclass=\"StartStatus-tooltip\" data-trigger=\"hover\"" +
                                "class=\"Form-tab Form-tab--disabled\">" + (collection.title || collection.editTitle) +
                                "</div>\n";
                        }

                        for (itm in this.form.relatedButtons) {
                            button = this.form.relatedButtons[itm];

                            // Build button HTML
                            html += "<button type=\"button\" ";
                            html += "class=\"btn btn-sm Form-tab--disabled";
                            html += (button['class']) ? " " + button['class'] : "";
                            html += "\" ";
                            html += "id=\"" + this.form.name + "_" + itm + "_btn\" ";

                            if(button.ngShow){
                                html += this.attr(button, 'ngShow');
                            }
                            if(button.awToolTip) {
                                html += " aw-tool-tip='" + button.awToolTip + "' data-placement='" + button.dataPlacement + "' data-tip-watch='" + button.dataTipWatch + "'";
                            }
                            html += ">";
                            html += " " + button.label + "</button>\n";
                        }
                    }
                    html += "</div>";//tabHolder
                }

                if(!_.isEmpty(this.form.related) && this.mode === "edit"){
                    html += `<div class="Form-tabSection" ng-class="{'is-selected' : $state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.$current.data.formChildState }">`;
                }

                html += "<form class=\"Form";
                html += (this.form.horizontal) ? "form-horizontal" : "";
                html += (this.form['class']) ? ' ' + this.form['class'] : '';
                html += "\" name=\"" + this.form.name + "_form\" id=\"" + this.form.name + "_form\" autocomplete=\"off\" novalidate>\n";
                html += "<div ng-show=\"flashMessage != null && flashMessage != undefined\" class=\"alert alert-info\">{{ flashMessage }}</div>\n";

                    var currentSubForm;
                    var hasSubFormField;
                    // original, single-column form
                    section = '';
                    group = '';
                    for (fld in this.form.fields) {
                        field = this.form.fields[fld];
                        if (!(options.modal && field.excludeModal)) {
                            if (field.group && field.group !== group) {
                                if (group !== '') {
                                    html += "</div>\n";
                                }
                                html += "<div class=\"well\">\n";
                                html += "<h5>" + field.group + "</h5>\n";
                                group = field.group;
                            }
                            if (field.section && field.section !== section) {
                                if (section !== '') {
                                    html += "</div>\n";
                                } else {
                                    html += "</div>\n";
                                    html += "<div id=\"" + this.form.name + "-collapse\" class=\"jqui-accordion-modal\">\n";
                                }
                                sectionShow = (this.form[field.section + 'Show']) ? " ng-show=\"" + this.form[field.section + 'Show'] + "\"" : "";
                                html += "<h3" + sectionShow + ">" + field.section + "</h3>\n";
                                html += "<div" + sectionShow + ">\n";
                                section = field.section;
                            }

                            // To hide/show the subform when the value changes on parent
                            if (field.hasSubForm === true) {
                              hasSubFormField = fld;
                            }

                            // Add a subform container
                            if(field.subForm && currentSubForm === undefined) {
                                currentSubForm = field.subForm;
                                var subFormTitle = this.form.subFormTitles[field.subForm];

                                html += '<div class="Form-subForm '+ currentSubForm + '" ng-hide="'+ hasSubFormField + '.value === undefined || ' + field.hideSubForm + '"> ';
                                html += '<span class="Form-subForm--title">'+ subFormTitle +'</span>';
                            }
                            else if (!field.subForm && currentSubForm !== undefined) {
                               currentSubForm = undefined;
                               html += '</div> ';
                            }

                            html += this.buildField(fld, field, options, this.form);
                           // console.log('*********')
                           // console.log(html)

                        }
                    }
                    if (currentSubForm) {
                      currentSubForm = undefined;
                      html += '</div>';
                    }
                    if (section !== '') {
                        html += "</div>\n</div>\n";
                    }
                    if (group !== '') {
                        html += "</div>\n";
                    }

                html += "</form>\n";

                //buttons
                if ((options.showButtons === undefined || options.showButtons === true) && !this.modal) {
                    if (this.has('buttons')) {

                        html += "<div class=\"buttons Form-buttons\" ";
                        html += "id=\"" + this.form.name + "_controls\" ";
                        if (options.mode === 'edit' && !_.isEmpty(this.form.related)) {
                            html += `ng-show="$state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.$current.data.formChildState || $state.matches('lookup') "`;
                        }
                        html += ">\n";

                        if (this.form.horizontal) {
                            offset = 2;
                            if (this.form.buttons.labelClass) {
                                offset = parseInt(this.form.buttons.labelClass.replace(/[A-Z,a-z,-]/g, ''));
                            }
                            width = 12 - offset;
                            html += "<div class=\"col-lg-offset-" + offset + " col-lg-" + width + ">\n";
                        }

                        for (btn in this.form.buttons) {
                            if (typeof this.form.buttons[btn] === 'object') {
                                button = this.form.buttons[btn];

                                if (button.component === 'at-launch-template') {
                                    html += `<at-launch-template template="${button.templateObj}" ng-show="${button.ngShow}" disabled="${button.ngDisabled}" show-text-button="${button.showTextButton}"></at-launch-template>`;
                                } else {
                                    // Set default color and label for Save and Reset
                                    if (btn === 'save') {
                                        button.label = i18n._('Save');
                                        button['class'] = 'Form-saveButton';
                                    }
                                    if (btn === 'select') {
                                        button.label = i18n._('Select');
                                        button['class'] = 'Form-saveButton';
                                    }
                                    if (btn === 'cancel') {
                                        button.label = i18n._('Cancel');
                                        button['class'] = 'Form-cancelButton';
                                    }
                                    if (btn === 'close') {
                                        button.label = i18n._('Close');
                                        button['class'] = 'Form-cancelButton';
                                    }
                                    if (btn === 'launch') {
                                        button.label = i18n._('Launch');
                                        button['class'] = 'Form-launchButton';
                                    }
                                    if (btn === 'add_survey') {
                                        button.label = i18n._('Add Survey');
                                        button['class'] = 'Form-surveyButton';
                                    }
                                    if (btn === 'edit_survey') {
                                        button.label =  i18n._('Edit Survey');
                                        button['class'] = 'Form-surveyButton';
                                    }
                                    if (btn === 'view_survey') {
                                        button.label = i18n._('View Survey');
                                        button['class'] = 'Form-surveyButton';
                                    }
                                    if (btn === 'workflow_visualizer') {
                                        button.label = i18n._('Workflow Visualizer');
                                        button['class'] = 'Form-primaryButton';
                                    }

                                    // Build button HTML
                                    html += "<button type=\"button\" ";
                                    html += "class=\"btn btn-sm";
                                    html += (button['class']) ? " " + button['class'] : "";
                                    html += "\" ";
                                    html += "id=\"" + this.form.name + "_" + btn + "_btn\" ";

                                    if(button.ngShow){
                                        html += this.attr(button, 'ngShow');
                                    }
                                    if (button.ngClick) {
                                        html += this.attr(button, 'ngClick');
                                    }
                                    if (button.ngClass) {
                                        html += this.attr(button, 'ngClass');
                                    }
                                    if (button.ngDisabled) {
                                        ngDisabled = (button.ngDisabled===true) ? `${this.form.name}_form.$invalid ||  ${this.form.name}_form.$pending`: button.ngDisabled;
                                        if (btn !== 'reset') {
                                            //html += "ng-disabled=\"" + this.form.name + "_form.$pristine || " + this.form.name + "_form.$invalid";

                                            if (button.disabled && button.disable !== true) {
                                                // Allow disabled to overrule ng-disabled. Used for permissions.
                                                // Example: system auditor can view but not update. Form validity
                                                // is no longer a concern but ng-disabled will update disabled
                                                // status on render so we stop applying it here.
                                            } else {
                                                html += "ng-disabled=\"" + ngDisabled;
                                                //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                                html += "\" ";
                                            }

                                        } else {
                                            //html += "ng-disabled=\"" + this.form.name + "_form.$pristine";
                                            //html += (this.form.allowReadonly) ? " || " + this.form.name + "ReadOnly == true" : "";
                                            //html += "\" ";
                                        }
                                    }
                                    if (button.disabled && button.disable !== true) {
                                        html += ` disabled="disabled" `;
                                    }
                                    if(button.awToolTip) {
                                        html += " aw-tool-tip='" + button.awToolTip + "' data-placement='" + button.dataPlacement + "' data-tip-watch='" + button.dataTipWatch + "'";
                                    }
                                    html += ">";
                                    html += " " + button.label + "</button>\n";
                                }
                            }
                        }
                        html += "</div><!-- buttons -->\n";

                        if (this.form.horizontal) {
                            html += "</div>\n";
                        }
                    }
                }

                if(!_.isEmpty(this.form.related) && this.mode === "edit"){
                    html += `</div>`;
                }

                if (this.form.include){
                    _.forEach(this.form.include, (template) =>{
                        html += `<div ng-include="'${template}'"></div>`;
                    });
                }
                // console.log(html);
                return this.wrapPanel(html, options.noPanel);
            },

            buildCollection: function (params) {
                // Currently, there are two ways we reference a list definition in a form
                // Permissions lists are defined with boilerplate JSON in model.related
                // this.GenerateCollection() is shaped around supporting this definition
                // Notifications lists contain a reference to the NotificationList object, which contains the list's JSON definition
                // However, Notification Lists contain fields that are only rendered by with generateList.build's chain
                // @extendme rip out remaining HTML-concat silliness and directivize ¯\_(ツ)_/¯
                this.form = params.form;
                var html = '',
                    collection = this.form.related[params.related];

                    if (collection.generateList) {
                        html += GenerateList.build({ mode: params.mode, list: collection});
                    }
                    else {
                        html += this.GenerateCollection({ form: this.form, related: params.related }, {mode: params.mode});
                    }

                return html;
            },

            GenerateCollection: function(params, options) {
                var html = '',
                    form = params.form,
                    itm = params.related,
                    collection = form.related[itm],
                    act, fld, cnt, base, fAction, width;

                if (collection.instructions) {
                    html += "<div class=\"alert alert-info alert-block\">\n";
                    html += "<button aria-label=\"{{'Close'|translate}}\" type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
                    html += "<strong>Hint: </strong>" + collection.instructions + "\n";
                    html += "</div>\n";
                }

                var actionButtons = "";
                Object.keys(collection.actions || {})
                    .forEach(act => {
                        actionButtons += ActionButton(collection
                            .actions[act]);
                    });
                var hideOnSuperuser = (hideOnSuperuser === true) ? true : false;
                if(actionButtons.length === 0 ){
                    // The search bar should be full width if there are no
                    // action buttons
                    width = "col-lg-12 col-md-12 col-sm-12 col-xs-12";
                }
                else {
                    width = "col-lg-8 col-md-8 col-sm-8 col-xs-12";
                }

                if(actionButtons.length>0){
                    html += `<div class="list-actions">
                            ${actionButtons}
                        </div>`;
                }

                // smart-search directive
                html += `
                <div
                    ng-hide="(${itm}.length === 0 && (searchTags | isEmpty)) || hideSmartSearch === true">
                        <smart-search
                            django-model="${itm}"
                            search-size="${width}"
                            base-path="${ collection.basePath }"
                            iterator="${collection.iterator}"
                            list="list"
                            collection="${collection.iterator}s"
                            dataset="${collection.iterator}_dataset"
                            search-tags="searchTags">
                        </smart-search>
                </div>
                    `;


                //html += "</div>";

                // Message for when a search returns no results.  This should only get shown after a search is executed with no results.
                html += `
                    <div
                        class="row"
                        ng-show="${itm}.length === 0 && !(searchTags | isEmpty)">
                        <div class="col-lg-12 List-searchNoResults" translate>`;
                html += i18n._('No records matched your search.');
                html += `</div>
                    </div>
                `;

                // Show the "no items" box when loading is done and the user isn't actively searching and there are no results
                var emptyListText = (collection.emptyListText) ? collection.emptyListText : i18n._("PLEASE ADD ITEMS TO THIS LIST");
                html += `<div ng-hide="is_superuser">`;
                html += `<div class="List-noItems" ng-show="${itm}.length === 0 && (searchTags | isEmpty)"> ${emptyListText} </div>`;
                html += '</div>';

                html += `
                    <div class="List-noItems" ng-show="is_superuser">
                        ${i18n._('System Administrators have access to all ' + collection.iterator + 's')}
                    </div>
                `;

                // Start the list
                html += `
                <div class="list-wrapper"
                    ng-show="${collection.iterator}s.length > 0 && !is_superuser">
                    <div id="${itm}_table" class="${collection.iterator} List-table">
                        <div class="d-flex List-tableHeaderRow">
                `;
                for (fld in collection.fields) {
                    html += `<div class="List-tableHeader list-header ${collection.fields[fld].columnClass}"
                        id="${collection.iterator}-${fld}-header"
                        base-path="${collection.basePath}"
                        collection="${collection.name}"
                        dataset="${collection.iterator}_dataset"
                        column-sort
                        column-field="${fld}"
                        column-iterator="${collection.iterator}"
                        column-no-sort="${collection.fields[fld].nosort}"
                        column-label="${collection.fields[fld].label}">
                        ${collection.fields[fld].label}
                        </div>`;
                }
                if (collection.fieldActions) {
                    html += `<div class="List-tableHeader List-tableHeader--actions ${collection.fieldActions.columnClass}">${i18n._('Actions')}</div>`;
                }
                html += "</div>";

                html += "<div class=\"d-flex List-tableRow\" ng-repeat=\"" + collection.iterator + " in " + itm + "\" ";
                html += "id=\"{{ " + collection.iterator + ".id }}\">\n";
                if (collection.index === undefined || collection.index !== false) {
                    html += "<div class=\"List-tableCell";
                    html += (collection.fields[fld].class) ? collection.fields[fld].class : "";
                    html += "\">{{ $index + ((" + collection.iterator + "_page - 1) * " +
                        collection.iterator + "_page_size) + 1 }}.</div>\n";
                }
                cnt = 1;
                base = (collection.base) ? collection.base : itm;
                base = base.replace(/^\//, '');
                for (fld in collection.fields) {
                    if (!collection.fields[fld].searchOnly) {
                        cnt++;
                        html += Column({
                            list: collection,
                            fld: fld,
                            options: options,
                            base: base
                        });
                    }
                }

                // Row level actions
                if (collection.fieldActions) {
                    html += `<div class="List-actionsContainer ${collection.fieldActions.columnClass}"><div class="List-tableCell List-actionButtonCell actions">`;
                    for (act in collection.fieldActions) {
                        if (act !== 'columnClass') {
                            fAction = collection.fieldActions[act];
                            html += "<button aria-label=\"{{act}}\" id=\"" + ((fAction.id) ? fAction.id : collection.iterator + "-" + `{{${collection.iterator}.id}}` + "-" + act + "-action") + "\" ";
                            html += (fAction.awToolTip) ? 'aw-tool-tip="' + fAction.awToolTip + '"' : '';
                            html += (fAction.dataPlacement) ? 'data-placement="' + fAction.dataPlacement + '"' : '';
                            html += (fAction.href) ? "href=\"" + fAction.href + "\" " : "";
                            html += (fAction.ngClick) ? this.attr(fAction, 'ngClick') : "";
                            html += (fAction.ngHref) ? this.attr(fAction, 'ngHref') : "";
                            html += (fAction.ngShow) ? this.attr(fAction, 'ngShow') : "";
                            html += " class=\"List-actionButton ";
                            html += (act === 'delete') ? "List-actionButton--delete" : "";
                            html += "\"";

                            html += ">";
                            if (fAction.iconClass) {
                                html += "<i class=\"" + fAction.iconClass + "\"></i>";
                            } else {
                                html += SelectIcon({
                                    action: act
                                });
                            }
                            // html += SelectIcon({ action: act });
                            //html += (fAction.label) ? "<span class=\"list-action-label\"> " + fAction.label + "</span>": "";
                            html += "</button>";
                        }
                    }
                    html += "</div></div>";
                    html += "</div>\n";
                }

                // Message for loading
                html += "<div ng-show=\"" + collection.iterator + "Loading == true\">\n";
                html += "<div colspan=\"" + cnt + "\"><div class=\"loading-info\">" + i18n._("Loading...") + "</div></div>\n";
                html += "</div>\n";

                // End List
                html += "</div>\n";
                //html += "</div>\n"; // close well
                html += "</div>\n"; // close list-wrapper div

                html += `<paginate
                    base-path="${collection.basePath}"
                    dataset="${collection.iterator}_dataset"
                    collection="${collection.iterator}s"
                    iterator="${collection.iterator}"
                    query-set="${collection.iterator}_queryset"
                    ng-hide="hidePagination">`;
                return html;
            },
        };

        function createCheckbox (options) {
            let ngChange = options.ngChange ? `ng-change="${options.ngChange}"` : '';
            let ngDisabled = options.ngDisabled ? `ng-disabled="${options.ngDisabled}"` : '';
            let ngModel = options.ngModel ? `ng-model="${options.ngModel}"` : '';
            let ngShow = options.ngShow ? `ng-show="${options.ngShow}"` : '';

            return `
                <div class="form-check Form-checkbox Form-checkbox--subCheckbox">
                    <label class="form-check-label" ${ngShow}>
                        <input class="form-check-input" type="checkbox" id="${options.id}" ${ngModel} ${ngChange} ${ngDisabled} />
                        ${options.text}
                    </label>
                </div>`;
        }

    }
]);
