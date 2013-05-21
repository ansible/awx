/*********************************************
 *  Copyright (c) 2013 AnsibleWorks, Inc.
 *
 *  JobTemplateHelper
 * 
 */
angular.module('JobTemplateHelper', [ 'RestServices', 'Utilities', 'CredentialFormDefinition' ])
    .factory('PromptPasswords',['CredentialForm', '$compile', 'Rest', function(JobTemplateForm, $compile, Rest) {
    return function(params) {
        
        var scope = params.scope; 
        var passwords = params.passwords;
        var start_url = params.start_url;
        var form = JobTemplateForm;
        var html = '';
        var field, element, dialogScope, fld;
        
        scope.startJob = function() {
            $('#password-modal').modal('hide');
            var pswd = {};  
            $('.password-field').each(function(index) {
                pswd[$(this).attr('name')] = $(this).val();
                });
            Rest.setUrl(start_url); 
            Rest.post(pswd)
                .success( function(data, status, headers, config) {
                    $location.path('/jobs');
                    })
                .error( function(data, status, headers, config) { 
                    ProcessErrors(scope, data, status, null,
                        { hdr: 'Error!', msg: 'Failed to start job. POST returned status: ' + status });
                    });
            }
        
        html += html += "<form class=\"form-horizontal\" name=\"password_form\" novalidate>\n";    
        for (var i=0; i < passwords.length; i++) {
            // Add the password field
            field = form.fields[passwords[i]];
            fld = passwords[i];
            scope[fld] = '';
            html += "<div class=\"control-group\">\n";
            html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
            html += "<div class=\"controls\">\n"; 
            html += "<input type=\"password\" ";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += "class=\"password-field\" ";
            html += "required ";
            html += "/>";
            html += "<br />\n";
            // Add error messages
            html += "<span class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " + 
                "password_form." + fld + ".$error.required\">A value is required!</span>\n";
            html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
            html += "</div>\n";
            html += "</div>\n";
         
            // Add the related confirm field
            fld = field.associated;
            field = form.fields[field.associated];
            scope[fld] = '';
            html += "<div class=\"control-group\">\n";
            html += "<label class=\"control-label\" for=\"" + fld + '">' + field.label + '</label>' + "\n";
            html += "<div class=\"controls\">\n"; 
            html += "<input type=\"password\" ";
            html += "ng-model=\"" + fld + '" ';
            html += 'name="' + fld + '" ';
            html += "required ";
            html += (field.awPassMatch) ? "awpassmatch=\"" + field.associated + "\" " : "";
            html += "/>";
            html += "<br />\n";
            // Add error messages
            html += "<span class=\"error\" ng-show=\"password_form." + fld + ".$dirty && " + 
                "password_form." + fld + ".$error.required\">A value is required!</span>\n";     
            if (field.awPassMatch) {
               html += "<span class=\"error\" ng-show=\"password_form." + fld + 
                   ".$error.awpassmatch\">Must match Password value</span>\n";
            }
            html += "<span class=\"error api-error\" ng-bind=\"" + fld + "_api_error\"></span>\n";
            html += "</div>\n";
            html += "</div>\n";
        }
        html += "</form>\n";
        element = angular.element(document.getElementById('password-body'));
        element.html(html);
        $compile(element.contents())(scope);
        $('#password-modal').modal();
        }
    }]);

























