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
 * | genMD5 | true or false. If true, places the field in an input group with a button that when clicked replaces the field contents with an MD5 has key. Used with host_config_key on the job templates detail page. |
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
 * | type | String containing one of the following types defined in buildField: alertblock, hidden, text, password, email, textarea, select, number, checkbox, checkbox_group, radio, radio_group, lookup, custom. |
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
 * Applying CodeMirror to the text area is handled by ParseTypeChange() found in helpers/Parse.js. Within the controller will be a call to ParseTypeChange that creates the CodeMirror object and sets up the required $scope methods for handles getting, settting and type conversion.
 */

import GeneratorHelpers from './generator-helpers';
import listGenerator from './list-generator/main';

export default
angular.module('FormGenerator', [GeneratorHelpers.name, 'Utilities', listGenerator.name])

.factory('GenerateForm', ['$rootScope', '$location', '$compile', 'generateList',
    'Attr', 'Icon', 'Column',
    'NavigationLink', 'HelpCollapse', 'DropDown', 'Empty', 'SelectIcon',
    'Store', 'ActionButton', '$log', 'i18n', '$timeout',
    function ($rootScope, $location, $compile, GenerateList,
        Attr, Icon, Column, NavigationLink, HelpCollapse,
        DropDown, Empty, SelectIcon, Store, ActionButton, $log, i18n, $timeout) {
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
            // Also wraps mess of generated HTML in a .Panel
            wrapPanel(html){
                return `<div class="Panel">
                ${html}
                <div ui-view="related"></div>
                <div ui-view="modal"></div>
                </div>`;
            },

            buildHTML: function(form, options) {
                // Get HTML without actually injecting into DOM. Caller is responsible for any injection.
                // Example:
                //   html = GenerateForm.buildHTML(JobVarsPromptForm, { mode: 'edit', modal: true, scope: scope });

                this.mode = options.mode;
                this.modal = (options.modal) ? true : false;
                this.setForm(form);
                return this.build(options);
            },

            applyDefaults: function (form, scope) {
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
                    if (f.chkPass && scope[form.name + '_form'][fld] && $AnsibleConfig) {
                        if ($AnsibleConfig.password_length) {
                            scope[form.name + '_form'][fld].$setValidity('password_length', true);
                        }
                        if ($AnsibleConfig.password_hasLowercase) {
                            scope[form.name + '_form'][fld].$setValidity('hasLowercase', true);
                        }
                        if ($AnsibleConfig.password_hasUppercase) {
                            scope[form.name + '_form'][fld].$setValidity('hasUppercase', true);
                        }
                        if ($AnsibleConfig.password_hasNumber) {
                            scope[form.name + '_form'][fld].$setValidity('hasNumber', true);
                        }
                        if ($AnsibleConfig.password_hasSymbol) {
                            scope[form.name + '_form'][fld].$setValidity('hasSymbol', true);
                        }
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
                    this.applyDefaults();
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


            buildHelpCollapse: function (collapse_array) {
                var html = '',
                    params = {}, i;
                for (i = 0; i < collapse_array.length; i++) {
                    params.hdr = collapse_array[i].hdr;
                    params.content = collapse_array[i].content;
                    params.idx = this.accordion_count++;
                    params.show = (collapse_array[i].show) ? collapse_array[i].show : null;
                    params.ngHide = (collapse_array[i].ngHide) ? collapse_array[i].ngHide : null;
                    params.bind = (collapse_array[i].ngBind) ? collapse_array[i].ngBind : null;
                    html += HelpCollapse(params);
                }
                return html;
            },

            buildHeaderField: function(key, field, options, form){
                var html = '';
                // extend these blocks to include elements similarly buildField()
                if (field.type === 'toggle'){
                    html += "<div class=\"Field-header--" + key;
                    html += (field['class']) ? " " + field['class'] : "";
                    html += " " + field.columnClass;
                    html += "\"><div class='ScheduleToggle' ng-class='{\"is-on\": " + form.iterator + ".";
                    html += (field.flag) ? field.flag : "enabled";
                    html += "\}' aw-tool-tip='" + field.awToolTip + "' data-placement='" + field.dataPlacement + "' data-tip-watch='" + field.dataTipWatch + "'><div ng-show='" + form.iterator + "." ;
                    html += (field.flag) ? field.flag : 'enabled';
                    html += "' class='ScheduleToggle-switch is-on' ng-click='" + field.ngClick + "'>ON</div><div ng-show='!" + form.iterator + "." ;
                    html += (field.flag) ? field.flag : "enabled";
                    html += "' class='ScheduleToggle-switch' ng-click='" + field.ngClick + "'>OFF</div></div></div>";
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

                function buildCheckbox(form, field, fld, idx, includeLabel) {
                    var html = '',
                        label = (includeLabel !== undefined && includeLabel === false) ? false : true;

                    if (label) {
                        html += "<label class=\"";
                        html += (field.inline === undefined || field.inline === true) ? "checkbox-inline" : "";
                        html += (field.labelClass) ? " " + field.labelClass : "";
                        html += "\"";
                        html += (field.ngShow) ? " ng-show=\"" +field.ngShow + "\" " : "";
                        html += ">";
                    }

                    html += "<input type=\"checkbox\" ";
                    html += Attr(field, 'type');
                    html += "ng-model=\"" + fld + '" ';
                    html += "name=\"" + fld + '" ';
                    html += (field.ngChange) ? Attr(field, 'ngChange') : "";
                    html += "id=\"" + form.name + "_" + fld + "_chbox\" ";
                    html += (idx !== undefined) ? "_" + idx : "";
                    html += "class=\"";
                    html += "\"";
                    html += (field.trueValue !== undefined) ? Attr(field, 'trueValue') : "";
                    html += (field.falseValue !== undefined) ? Attr(field, 'falseValue') : "";
                    html += (field.checked) ? "checked " : "";
                    html += (field.readonly) ? "disabled " : "";
                    html += (field.ngChange) ? "ng-change=\"" +field.ngChange + "\" " : "";
                    html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                    html += " > ";

                    if (label) {
                        html += field.label + " ";
                        html += (field.awPopOver) ? Attr(field, 'awPopOver', fld) : "";
                        html += "</label>\n";
                    }

                    return html;
                }

                function label() {
                    var html = '';
                    if (field.label || field.labelBind) {
                        html += "<label class=\"";
                        html += (field.labelClass) ? field.labelClass : "";
                        html += `${field.required ? ' prepend-asterisk ' : ''}`;
                        html += (horizontal) ? " " + getLabelWidth() : "Form-inputLabelContainer ";
                        html += "\" ";
                        html += (field.labelNGClass) ? "ng-class=\"" + field.labelNGClass + "\" " : "";
                        html += "for=\"" + fld + '">\n';
                        html += (field.icon) ? Icon(field.icon) : "";
                        if (field.labelBind) {
                            html += "\t\t<span ng-class=class=\"Form-inputLabel\" ng-bind=\"" + field.labelBind + "\">\n\t\t</span>";
                        } else {
                            html += "\t\t<span class=\"Form-inputLabel\">\n\t\t\t" + field.label + "\n\t\t</span>";
                        }
                        html += (field.awPopOver && !field.awPopOverRight) ? Attr(field, 'awPopOver', fld) : "";
                        html += (field.hintText) ? "\n\t\t<span class=\"label-hint-text\">\n\t\t\t<i class=\"fa fa-info-circle\">\n\t\t\t</i>\n\t\t\tHint: " + field.hintText + "\n\t\t</span>" : "";
                        // Variable editing
                        if (fld === "variables" || fld === "extra_vars" || _.last(fld.split('_')) === 'variables' || fld === 'source_vars') {
                            html += "<div class=\"parse-selection\" id=\"" + form.name + "_" + fld + "_parse_type\">" +
                                "<input type=\"radio\" ng-disabled=\"disableParseSelection\" ng-model=\"";
                            html += (field.parseTypeName) ? field.parseTypeName : 'parseType';
                            html += "\" value=\"yaml\" ng-change=\"parseTypeChange('" + ((field.parseTypeName) ? field.parseTypeName : 'parseType') + "', '" + fld + "'" + ")\"> <span class=\"parse-label\">YAML</span>\n";
                            html += "<input type=\"radio\" ng-disabled=\"disableParseSelection\" ng-model=\"";
                            html += (field.parseTypeName) ? field.parseTypeName : 'parseType';
                            html += "\" value=\"json\" ng-change=\"parseTypeChange('" + ((field.parseTypeName) ? field.parseTypeName : 'parseType')+ "', '" + fld + "'" + ")\"> <span class=\"parse-label\">JSON</span>\n";
                            html += "</div>\n";
                        }

                        if (field.labelAction) {
                            let action = field.labelAction;
                            let href = action.href || "";
                            let ngClick = action.ngClick || "";
                            let cls = action["class"] || "";
                            html += `<a class="Form-labelAction ${cls}" href="${href}" ng-click="${ngClick}">${action.label}</a>`;
                        }
                        html += "\n\t</label>\n";
                    }
                    return html;
                }

                if (field.type === 'toggle'){
                    html += "<td class=\"List-tableCell " + fld + "-column";
                    html += (field['class']) ? " " + field['class'] : "";
                    html += " " + field.columnClass;
                    html += "\"><div class='ScheduleToggle' ng-class='{\"is-on\": " + form.iterator + ".";
                    html += (field.flag) ? field.flag : "enabled";
                    html += "\}' aw-tool-tip='" + field.awToolTip + "' data-placement='" + field.dataPlacement + "' data-tip-watch='" + field.dataTipWatch + "'><div ng-show='" + form.iterator + "." ;
                    html += (field.flag) ? field.flag : 'enabled';
                    html += "' class='ScheduleToggle-switch is-on' ng-click='" + field.ngClick + "'>ON</div><div ng-show='!" + form.iterator + "." ;
                    html += (field.flag) ? field.flag : "enabled";
                    html += "' class='ScheduleToggle-switch' ng-click='" + field.ngClick + "'>OFF</div></div></td>";
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
                        "<button type=\"button\" class=\"close\" data-dismiss=\"alert\" aria-hidden=\"true\">&times;</button>\n" : "";
                    html += field.alertTxt;
                    html += "</div>\n";
                    html += "</div>\n";
                    html += "</div>\n";
                }

                if (field.type === 'hidden') {
                    if ((options.mode === 'edit' && field.includeOnEdit) ||
                        (options.mode === 'add' && field.includeOnAdd)) {
                        html += "<input type=\"hidden\" ng-model=\"" + fld + "\" name=\"" + fld + "\" />";
                    }
                }

                if ((!field.readonly) || (field.readonly && options.mode === 'edit')) {

                    if((field.excludeMode === undefined || field.excludeMode !== options.mode) && field.type !== 'alertblock' && field.type !== 'workflow-chart') {


                    html += "<div class='form-group Form-formGroup ";
                    html += (field.type === "checkbox") ? "Form-formGroup--checkbox" : "";
                    html += (field['class']) ? (field['class']) : "";
                    html += "'";
                    html += (field.ngShow) ? this.attr(field, 'ngShow') : "";
                    html += (field.ngHide) ? this.attr(field, 'ngHide') : "";
                    html += (field.awFeature) ? "aw-feature=\"" + field.awFeature + "\" " : "";
                    html += ">\n";

                    //text fields
                    if (field.type === 'text' || field.type === 'password' || field.type === 'email') {
                        html += label();
                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += (field.clear || field.genMD5) ? "<div class=\"input-group\">\n" : "";

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
                            html += ">\n";
                        }

                        if (field.clear) {
                            html += "<span class=\"input-group-btn\"><button type=\"button\" ";
                            html += "id=\"" + this.form.name + "_" + fld + "_clear_btn\" ";
                            html += "class=\"btn btn-default\" ng-click=\"clear('" + fld + "','" + field.associated + "')\" " +
                                "aw-tool-tip=\"Clear " + field.label + "\" id=\"" + fld + "-clear-btn\" ";
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += " ><i class=\"fa fa-undo\"></i></button>\n";
                            html += "</span>\n</div>\n";
                        }

                        if (field.genMD5) {
                            html += "<span class=\"input-group-btn\"><button type=\"button\" class=\"btn btn-default Form-lookupButton\" ng-click=\"genMD5('" + fld + "')\" " +
                                "aw-tool-tip=\"Generate " + field.label + "\" data-placement=\"top\" id=\"" + this.form.name + "_" + fld + "_gen_btn\">" +
                                "<i class=\"fa fa-magic\"></i></button></span>\n</div>\n";
                        }

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" + field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
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

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
                    }

                    //fields with sensitive data that needs to be obfuscated from view
                    if (field.type === 'sensitive') {
                        field.showInputInnerHTML = i18n._("Show");
                        field.inputType = "password";

                        html += "\t" + label();
                        if (field.hasShowInputButton) {
                            var tooltip = i18n._("Toggle the display of plaintext.");
                            field.toggleInput = function(id) {
                                var buttonId = id + "_show_input_button",
                                    inputId = id + "_input",
                                    buttonInnerHTML = $(buttonId).html();
                                if (buttonInnerHTML.indexOf("Show") > -1) {
                                    $(buttonId).html("Hide");
                                    $(inputId).attr("type", "text");
                                } else {
                                    $(buttonId).html("Show");
                                    $(inputId).attr("type", "password");
                                }
                            };
                            html += "\<div class='input-group";
                            html += (horizontal) ? " " + getFieldWidth() : "";
                            html += "'>\n";
                            // TODO: make it so that the button won't show up if the mode is edit, hasShowInputButton !== true, and there are no contents in the field.
                            html += "<span class='input-group-btn'>\n";
                            html += "<button type='button' class='btn btn-default show_input_button Form-passwordButton' ";
                            html += buildId(field, fld + "_show_input_button", this.form);
                            html += `aw-tool-tip='${tooltip}'} aw-tip-placement='top'`;
                            html += "tabindex='-1' ";
                            html += "ng-click='" + fld + "_field.toggleInput(\"#" + this.form.name + "_" + fld + "\")'";
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
                            html += buildId(field, fld + "_input", this.form);
                            html += "type='password' ";
                            html += "ng-model=\"" + fld + '" ';
                            html += 'name="' + fld + '" ';

                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += buildId(field, fld, this.form);

                            html += (field.controlNGClass) ? "ng-class='" + field.controlNGClass + "' " : "";
                            html += "class='form-control Form-textInput";
                            html += "' ";
                            html += (field.chkPass) ? "chk-pass " : "";

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
                            html += ">\n";
                        }

                        html += "</div>\n";

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            if (field.subCheckbox.ngDisabled) {
                                html += "ng-disabled='" + field.subCheckbox.ngDisabled + "'";
                            }
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
                        }

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
                            error_message = error_message = i18n._("This value does not match the password you entered previously.  Please confirm that password.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-passmatch-error' ng-show='" + this.form.name + "_form." + fld +
                                `.$error.awpassmatch'>${error_message}</div>`;
                        }
                        if (field.awValidUrl) {
                            error_message = i18n._("Please enter a URL that begins with ssh, http or https.  The URL may not contain the '@' character.");
                            html += "<div class='error' id='" + this.form.name + "-" + fld + "-url-error' ng-show='" + this.form.name + "_form." + fld +
                                `.$error.awvalidurl'>${error_message}</div>`;
                        }
                        if (field.chkPass && $AnsibleConfig) {
                            // password strength
                            if ($AnsibleConfig.password_length) {
                                error_message = i18n.format(i18n._("Your password must be %d characters long."), $AnsibleConfig.password_length);
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    `.$error.password_length">${error_message}</div>`;
                            }
                            if ($AnsibleConfig.password_hasLowercase) {
                                error_message = i18n._("Your password must contain a lowercase letter.");
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    `.$error.hasLowercase">${error_message}</div>`;
                            }
                            if ($AnsibleConfig.password_hasUppercase) {
                                error_message = i18n._("Your password must contain an uppercase letter.");
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    `.$error.hasUppercase">${error_message}</div>`;
                            }
                            if ($AnsibleConfig.password_hasNumber) {
                                error_message = i18n._("Your password must contain a number.");
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    `.$error.hasNumber">${error_message}</div>`;
                            }
                            if ($AnsibleConfig.password_hasSymbol) {
                                i18n.format(i18n._("Your password must contain one of the following characters: %s"), "`~!@#$%^&*()_-+=|}\]{\[;:\"\'?\/>.<,");
                                html += "<div class=\"error\" ng-show=\"" + this.form.name + '_form.' + fld +
                                    `.$error.hasSymbol">${error_message}</div>`;
                            }
                        }

                        html += "<div class='error api-error' id='" + this.form.name + "-" + fld + "-api-error' ng-bind='" + fld + "_api_error'>\n</div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';
                    }

                    //textarea fields
                    if (field.type === 'textarea') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<textarea ";
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
                        html += (field.readonly || field.showonly) ? "readonly " : "";
                        html += (field.awDropFile) ? "aw-drop-file " : "";
                        if(field.awRequiredWhen) {
                            html += field.awRequiredWhen.init ? "data-awrequired-init=\"" + field.awRequiredWhen.init + "\" " : "";
                            html += field.awRequiredWhen.reqExpression ? "aw-required-when=\"" + field.awRequiredWhen.reqExpression + "\" " : "";
                            html += field.awRequiredWhen.alwaysShowAsterisk ? "data-awrequired-always-show-asterisk=true " : "";
                        }
                        html += "aw-watch ></textarea>\n";

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            if (field.subCheckbox.ngDisabled) {
                                html += "ng-disabled='" + field.subCheckbox.ngDisabled + "'";
                            }
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
                        }

                        // Add error messages
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : "Please enter a value.") + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //select field
                    if (field.type === 'select') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<div class=\"Form-dropDownContainer\">\n";
                        html += "<select ";
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
                                // Add a custom default select 'value' (default text)
                            html += (field.defaultText) ? field.defaultText : i18n.format(i18n._("Choose a %s"), field.label.toLowerCase());
                            html += "</option>\n";
                        }

                        html += "</select>\n";
                        html += "</div>\n";

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            if (field.subCheckbox.ngDisabled) {
                                html += "ng-disabled='" + field.subCheckbox.ngDisabled + "'";
                            }
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
                        }

                            // Add error messages
                        if (field.required || field.awRequiredWhen) {
                                html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                    this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : "Please select a value.");
                                if (field.includePlaybookNotFoundError) {
                                    html += "  <span ng-show=\"playbookNotFound\">Playbook {{ job_template_obj.playbook }} not found for project.</span>\n";
                                }
                                html += "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
                    }

                    //number field
                    if (field.type === 'number') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += "<input ";
                        html += (field.spinner) ? "" : "type=\"text\" ";
                        html += "\" value=\"" + field['default'] + "\" ";
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
                        html += " >\n";

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
                        }

                        // Add error messages
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : "Please select a value.") + "</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Please enter a number.</div>\n";
                        }
                        if (field.min !== undefined || field.max !== undefined) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Please enter a number greater than " + field.min;
                            html += (field.max !== undefined) ? " and less than " + field.max + "." : ".";
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
                                this.form.name + '_form.' + fld + ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : "Please select at least one value.") + "</div>\n";
                        }
                        if (field.integer) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-integer-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.integer\">Please select a number.</div>\n";
                        }
                        if (field.min || field.max) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-minmax-error\" ng-show=\"" + this.form.name + '_form.' + fld + ".$error.min || " +
                                this.form.name + '_form.' + fld + ".$error.max\">Please select a number between " + field.min + " and " +
                                field.max + "</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
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
                        html += "<label>";
                        html += buildCheckbox(this.form, field, fld, undefined, false);
                        html += (field.icon) ? Icon(field.icon) : "";
                        if (field.labelBind) {
                            html += "\t\t<span class=\"Form-inputLabel\" ng-bind=\"" + field.labelBind + "\">\n\t\t</span>";
                        } else {
                            html += "<span class=\"Form-inputLabel\">" + field.label + "</span>";
                        }

                        html += (field.awPopOver) ? this.attr(field, 'awPopOver', fld) : "";
                        html += "</label>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";
                        html += "</div><!-- checkbox -->\n";

                        if (horizontal) {
                            html += "</div>\n";
                        }

                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';
                    }

                    //radio group
                    if (field.type === 'radio_group') {

                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        for (i = 0; i < field.options.length; i++) {
                            html += "<label class=\"radio-inline\" ";
                            html += (field.options[i].ngShow) ? this.attr(field.options[i], 'ngShow') : "";
                            html += ">";
                            html += "<input type=\"radio\" ";
                            html += "name=\"" + fld + "\" ";
                            html += "value=\"" + field.options[i].value + "\" ";
                            html += "ng-model=\"" + fld + "\" ";
                            html += (field.ngChange) ? this.attr(field, 'ngChange') : "";
                            html += (field.readonly) ? "disabled " : "";
                            html += (field.required) ? "required " : "";
                            html += (field.ngDisabled) ? this.attr(field, 'ngDisabled') : "";
                            html += " > " + field.options[i].label + "\n";
                            html += "</label>\n";
                        }
                        if (field.required) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" +
                                this.form.name + '_form.' + fld + ".$dirty && " +
                                this.form.name + '_form.' + fld + ".$error.required\">Please select a value.</div>\n";
                        }
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" +
                            fld + "_api_error\"></div>\n";

                        // Add help panel(s)
                        html += (field.helpCollapse) ? this.buildHelpCollapse(field.helpCollapse) : '';

                        html += "</div>\n";
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
                        html += " > ";
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
                        let defaultLookupNgClick = `$state.go($state.current.name + '.${field.sourceModel}')`;
                        html += label();

                        html += "<div ";
                        html += (horizontal) ? "class=\"" + getFieldWidth() + "\"" : "";
                        html += ">\n";

                        html += `<div class="input-group">`;
                        html += "<span class=\"input-group-btn\">\n";
                        html += `<button type="button" class="Form-lookupButton btn btn-default" ng-click="${field.ngClick || defaultLookupNgClick}"
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
                        html += `ng-model-options="{ updateOn: 'default blur', debounce: { 'default': 300, 'blur': 0 } }"`;
                        html += " awlookup >\n";
                        html += "</div>\n";

                        if (field.subCheckbox) {
                            html += "<label class=\"checkbox-inline Form-subCheckbox\" ";
                            html += (field.subCheckbox.ngShow) ? "ng-show=\"" + field.subCheckbox.ngShow + "\" " : "";
                            html += ">";
                            html += "<input type=\"checkbox\" ng-model=\"" +
                                field.subCheckbox.variable + "\" ";
                            html += (field.subCheckbox.ngChange) ? "ng-change=\"" + field.subCheckbox.ngChange + "\" " : "";
                            html += (field.ngDisabled) ? "ng-disabled=\"" + field.ngDisabled + "\" " : "";
                            html += "id=\"" + this.form.name + "_" + fld + "_ask_chbox\" ";
                            html += ">";
                            html += field.subCheckbox.text ? field.subCheckbox.text : "";
                            html += "</label>";
                        }

                        // Add error messages
                        if (field.required || field.awRequiredWhen) {
                            html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-required-error\" ng-show=\"" +
                                this.form.name + '_form.' +
                                field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                                this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                                ".$error.required\">" + (field.requiredErrorMsg ? field.requiredErrorMsg : "Please select a value.") + "</div>\n";
                        }
                        html += "<div class=\"error\" id=\"" + this.form.name + "-" + fld + "-notfound-error\" ng-show=\"" +
                            this.form.name + '_form.' +
                            field.sourceModel + '_' + field.sourceField + ".$dirty && " +
                            this.form.name + '_form.' + field.sourceModel + '_' + field.sourceField +
                            ".$error.awlookup\">That value was not found.  Please enter or select a valid value.</div>\n";
                        html += "<div class=\"error api-error\" id=\"" + this.form.name + "-" + fld + "-api-error\" ng-bind=\"" + field.sourceModel + '_' + field.sourceField +
                            "_api_error\"></div>\n";
                        html += "</div>\n";
                    }

                    //custom fields
                    if (field.type === 'custom') {
                        html += label();
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
                var btn, button, fld, field, html = '', i, section, group,
                    tab, sectionShow, offset, width,ngDisabled, itm;

                // title and exit button
                if(!(this.form.showHeader !== undefined && this.form.showHeader === false)) {
                    html +=  "<div class=\"Form-header\">";
                    html += "<div class=\"Form-title\">";
                    html += (options.mode === 'edit') ? this.form.editTitle : this.form.addTitle;
                    if(this.form.name === "user"){
                        html+= "<span class=\"Form-title--is_superuser\" "+
                            "ng-show='is_superuser'>Admin</span>";
                        html+= "<span class=\"Form-title--is_system_auditor\" "+
                            "ng-show='is_system_auditor'>Auditor</span>";
                        html+= "<span class=\"Form-title--is_ldap_user\" "+
                            "ng-show='ldap_user'>LDAP</span>";
                        html+= "<span class=\"Form-title--is_external_account\" "+
                            "ng-show='external_account'>{{external_account}}</span>";
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
                        html += "<button class=\"Form-exit\" ng-click=\"formCancel()\">";
                        html += "<i class=\"fa fa-times-circle\"></i>";
                        html += "</button></div>\n";
                    }
                        html += "</div>"; //end of Form-header
                }

                if (!_.isEmpty(this.form.related) || !_.isEmpty(this.form.relatedButtons)) {
                    var collection, details = i18n._('Details');
                    html += "<div class=\"Form-tabHolder\">";

                    if(this.mode === "edit"){
                        html += `<div id="${this.form.name}_tab" class="Form-tab" ` +
                            `ng-click="$state.go('${this.form.stateTree}.edit')" ` +
                            `ng-class="{'is-selected': $state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.$curruent.data.lookup }">` +
                            `${details}</div>`;

                        for (itm in this.form.related) {
                            collection = this.form.related[itm];
                            html += `<div id="${itm}_tab" `+
                                `class="Form-tab" `+
                                `ng-click="$state.go('${this.form.stateTree}.edit.${itm}')" `;
                            if (collection.awToolTip){
                                html += `aw-tool-tip="${collection.awToolTip}" ` +
                                `aw-tip-placement="${collection.dataPlacement}" ` +
                                `data-tip-watch="${collection.dataTipWatch}" `;
                            }
                            html += `ng-class="{'is-selected' : $state.is('${this.form.activeEditState}.${itm}') || $state.is('${this.form.stateTree}.edit.${itm}')}" ` ;
                            if(this.form.related[itm].disabled){
                                html += `, 'Form-tab--disabled' : ${this.form.related[itm].disabled }`;
                            }
                            html +=  `}">${(collection.title || collection.editTitle)}</div>`;
                        }

                        for (itm in this.form.relatedButtons) {
                            button = this.form.relatedButtons[itm];

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
                            if (button.awFeature) {
                                html += this.attr(button, 'awFeature');
                            }
                            if (button.ngDisabled) {
                                ngDisabled = (button.ngDisabled===true) ? this.form.name+"_form.$invalid" : button.ngDisabled;
                                if (btn !== 'reset') {
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
                            html += "<div id=\"" + itm + "_tab\" "+ "aw-tool-tip=\"" +
                                collection.awToolTip + "\" aw-tip-placement=\"" + collection.dataPlacement + "\" " +
                                "data-container=\"body\" tooltipinnerclass=\"StartStatus-tooltip\" data-trigger=\"hover\"" +
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
                            html += "id=\"" + this.form.name + "_" + btn + "_btn\" ";

                            if(button.ngShow){
                                html += this.attr(button, 'ngShow');
                            }
                            if (button.awFeature) {
                                html += this.attr(button, 'awFeature');
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
                    html += `<div class="Form-tabSection" ng-class="{'is-selected' : $state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.$current.data.lookup }">`;
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
                               html += '</div></div> ';
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
                            html += `ng-show="$state.is('${this.form.activeEditState}') || $state.is('${this.form.stateTree}.edit') || $state.matches('lookup') "`;
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

                                // Set default color and label for Save and Reset
                                if (btn === 'save') {
                                    button.label = i18n._('Save');
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
                                if (btn === 'workflow_editor') {
                                    button.label = i18n._('Workflow Editor');
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
                                if (button.awFeature) {
                                    html += this.attr(button, 'awFeature');
                                }
                                if (button.ngDisabled) {
                                    ngDisabled = (button.ngDisabled===true) ? `${this.form.name}_form.$invalid ||  ${this.form.name}_form.$pending`: button.ngDisabled;
                                    if (btn !== 'reset') {
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
                        html += "</div><!-- buttons -->\n";

                        if (this.form.horizontal) {
                            html += "</div>\n";
                        }

                    }
                }
                if (this.form.include){
                    _.forEach(this.form.include, (template) =>{
                        html += `<div ng-include="'${template}'"></div>`;
                    });
                }
               // console.log(html)
                return this.wrapPanel(html);
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
                    html += "<button type=\"button\" class=\"close\" data-dismiss=\"alert\">&times;</button>\n";
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

                // smart-search directive
                html += `
                <div
                    ng-hide="${itm}.length === 0 && (${collection.iterator}_searchTags | isEmpty)">
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

                if(actionButtons.length>0){
                    html += `<div class="list-actions">
                            ${actionButtons}
                        </div>`;
                }
                //html += "</div>";

                // Message for when a search returns no results.  This should only get shown after a search is executed with no results.
                html += `
                    <div
                        class="row"
                        ng-show="${itm}.length === 0 && !(${collection.iterator}_searchTags | isEmpty)">
                        <div class="col-lg-12 List-searchNoResults">
                            No records matched your search.
                        </div>
                    </div>
                `;

                // Show the "no items" box when loading is done and the user isn't actively searching and there are no results
                var emptyListText = (collection.emptyListText) ? collection.emptyListText : "PLEASE ADD ITEMS TO THIS LIST";
                html += `<div ng-hide="is_superuser">`;
                html += `<div class="List-noItems" ng-show="${itm}.length === 0 && (${collection.iterator}_searchTags | isEmpty)"> ${emptyListText} </div>`;
                html += '</div>';

                html += `
                    <div class="List-noItems" ng-show="is_superuser">
                        System Administrators have access to all ${collection.iterator}s
                    </div>
                `;

                // Start the list
                html += `
                <div class="list-wrapper"
                    ng-show="${collection.iterator}s.length > 0 && !is_superuser">
                    <table id="${itm}_table" class="${collection.iterator} List-table">
                        <thead>
                        <tr class="List-tableHeaderRow">
                `;
                html += (collection.index === undefined || collection.index !== false) ? "<th class=\"col-xs-1\">#</th>\n" : "";
                for (fld in collection.fields) {
                    html += `<th class="List-tableHeader list-header ${collection.fields[fld].columnClass}"
                        id="${collection.iterator}-${fld}-header"
                        column-sort
                        column-field="${fld}"
                        column-iterator="${collection.iterator}"
                        column-no-sort="${collection.fields[fld].nosort}"
                        column-label="${collection.fields[fld].label}">
                        ${collection.fields[fld].label}
                        </th>`;
                }
                if (collection.fieldActions) {
                    html += "<th class=\"List-tableHeader List-tableHeader--actions\">Actions</th>\n";
                }
                html += "</tr>\n";
                html += "</thead>";
                html += "<tbody>\n";

                html += "<tr class=\"List-tableRow\" ng-repeat=\"" + collection.iterator + " in " + itm + "\" ";
                html += "ng-class-odd=\"'List-tableRow--oddRow'\" ";
                html += "ng-class-even=\"'List-tableRow--evenRow'\" ";
                html += "id=\"{{ " + collection.iterator + ".id }}\">\n";
                if (collection.index === undefined || collection.index !== false) {
                    html += "<td class=\"List-tableCell";
                    html += (collection.fields[fld].class) ? collection.fields[fld].class : "";
                    html += "\">{{ $index + ((" + collection.iterator + "_page - 1) * " +
                        collection.iterator + "_page_size) + 1 }}.</td>\n";
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
                    html += "<td class=\"List-actionsContainer\"><div class=\"List-tableCell List-actionButtonCell actions\">";
                    for (act in collection.fieldActions) {
                        fAction = collection.fieldActions[act];
                        html += "<button id=\"" + ((fAction.id) ? fAction.id : act + "-action") + "\" ";
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
                    html += "</div></td>";
                    html += "</tr>\n";
                }

                // Message for loading
                html += "<tr ng-show=\"" + collection.iterator + "Loading == true\">\n";
                html += "<td colspan=\"" + cnt + "\"><div class=\"loading-info\">Loading...</div></td>\n";
                html += "</tr>\n";

                // End List
                html += "</tbody>\n";
                html += "</table>\n";
                //html += "</div>\n"; // close well
                html += "</div>\n"; // close list-wrapper div

                html += `<paginate base-path="${collection.basePath}" dataset="${collection.iterator}_dataset" iterator="${collection.iterator}">`;
                return html;
            }
        };
    }
]);
