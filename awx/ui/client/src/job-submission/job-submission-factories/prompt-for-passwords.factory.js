export default
    function PromptForPasswords(CredentialForm) {
        return function(params) {
            var scope = params.scope,
            callback = params.callback || 'PasswordsAccepted',
            url = params.url,
            form = CredentialForm,
            fld, field,
            html=params.html || "";

            scope.passwords = params.passwords;

            html += "<div class=\"alert alert-info\">Launching this job requires the passwords listed below. Enter each password before continuing.</div>\n";

            scope.passwords.forEach(function(password) {
                // Prompt for password
                field = form.fields[password];
                fld = password;
                scope[fld] = '';
                html += "<div class=\"form-group\">\n";
                html += "<label for=\"" + fld + "\">";
                html += '<span class="Form-requiredAsterisk">*</span>';
                html += '<span>' + field.label + '</span>';
                html += "</label>\n";
                html += "<input type=\"password\" ";
                html += "ng-model=\"" + fld + '" ';
                html += 'name="' + fld + '" ';
                html += "class=\"password-field form-control input-sm\" ";
                html += (field.associated) ? "ng-change=\"clearPWConfirm('" + field.associated + "')\" " : "";
                html += "required ";
                html += " >";
                // Add error messages
                html += "<div class=\"error\" ng-show=\"job_launch_form." + fld + ".$dirty && " +
                "job_launch_form." + fld + ".$error.required\">Please enter a password.</div>\n";
                html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                html += "</div>\n";

                // Add the related confirm field
                if (field.associated) {
                    fld = field.associated;
                    field = form.fields[field.associated];
                    scope[fld] = '';
                    html += "<div class=\"form-group\">\n";
                    html += "<label for=\"" + fld + "\"> " + field.label + "</label>\n";
                    html += '<span class="Form-requiredAsterisk">*</span>';
                    html += "<input type=\"password\" ";
                    html += "ng-model=\"" + fld + '" ';
                    html += 'name="' + fld + '" ';
                    html += "class=\"form-control input-sm\" ";
                    html += "ng-change=\"checkStatus()\" ";
                    html += "required ";
                    html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
                    html += "/>";
                    // Add error messages
                    html += "<div class=\"error\" ng-show=\"job_launch_form." + fld + ".$dirty && " +
                    "job_launch_form." + fld + ".$error.required\">Please confirm the password.</span>\n";
                    html += (field.awPassMatch) ? "<span class=\"error\" ng-show=\"job_launch_form." + fld +
                    ".$error.awpassmatch\">This value does not match the password you entered previously.  Please confirm that password.</div>\n" : "";
                    html += "<div class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></div>\n";
                    html += "</div>\n";
                }
            });

            scope.$emit(callback, html, url);

            // Password change
            scope.clearPWConfirm = function (fld) {
                // If password value changes, make sure password_confirm must be re-entered
                scope[fld] = '';
                scope.job_launch_form[fld].$setValidity('awpassmatch', false);
                scope.checkStatus();
            };

            scope.checkStatus = function() {
                if (!scope.job_launch_form.$invalid) {
                    $('#password-accept-button').removeAttr('disabled');
                }
                else {
                    $('#password-accept-button').attr({ "disabled": "disabled" });
                }
            };
        };
    }

PromptForPasswords.$inject =
    [   'CredentialForm'   ];
