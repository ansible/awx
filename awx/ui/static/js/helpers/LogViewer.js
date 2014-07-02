/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewer.js
 *
 */

'use strict';

angular.module('LogViewerHelper', ['ModalDialog', 'Utilities', 'FormGenerator', 'VariablesHelper'])

    .factory('LogViewer', ['$location', '$compile', 'CreateDialog', 'GetJob', 'Wait', 'GenerateForm', 'LogViewerStatusForm', 'AddTable', 'AddTextarea',
    'LogViewerOptionsForm', 'EnvTable', 'GetBasePath', 'LookUpName', 'Empty', 'AddPreFormattedText', 'ParseVariableString', 'GetChoices',
    function($location, $compile, CreateDialog, GetJob, Wait, GenerateForm, LogViewerStatusForm, AddTable, AddTextarea, LogViewerOptionsForm, EnvTable,
    GetBasePath, LookUpName, Empty, AddPreFormattedText, ParseVariableString, GetChoices) {
        return function(params) {
            var parent_scope = params.scope,
                url = params.url,
                getIcon = params.getIcon,
                scope = parent_scope.$new(true),
                base = $location.path().replace(/^\//, '').split('/')[0],
                pieces;

            if (scope.removeModalReady) {
                scope.removeModalReady();
            }
            scope.removeModalReady = scope.$on('ModalReady', function() {
                Wait('stop');
                $('#logviewer-modal-dialog').dialog('open');
            });

            if (scope.removeJobReady) {
                scope.removeJobReady();
            }
            scope.removeJobReady = scope.$on('JobReady', function(e, data) {
                var key, resizeText, elem;
                $('#status-form-container').empty();
                $('#options-form-container').empty();
                $('#stdout-form-container').empty();
                $('#traceback-form-container').empty();
                $('#variables-container').empty();
                $('#source-container').empty();
                $('#logview-tabs li:eq(1)').hide();
                $('#logview-tabs li:eq(2)').hide();
                $('#logview-tabs li:eq(4)').hide();
                $('#logview-tabs li:eq(5)').hide();

                // Make sure subsequenct scope references don't bubble up to the parent
                for (key in LogViewerStatusForm.fields) {
                    scope[key] = '';
                }
                for (key in LogViewerOptionsForm.fields) {
                    scope[key] = '';
                }

                for (key in data) {
                    scope[key] = data[key];
                }
                scope.created_by = '';
                scope.job_template = '';

                if (data.related.created_by) {
                    pieces = data.related.created_by.replace(/^\//,'').replace(/\/$/,'').split('/');
                    scope.created_by = parseInt(pieces[pieces.length - 1],10);
                    LookUpName({
                        scope: scope,
                        scope_var: 'created_by',
                        url: GetBasePath('users') + scope.created_by + '/'
                    });
                }

                // For jobs link the name to the job parent
                if (base === 'jobs') {
                    if (data.type === 'job') {
                        scope.name_link = "job_template";
                        scope.job_template = data.unified_job_template;
                        scope.job_template_name = (data.summary_fields.job_template) ? data.summary_fields.job_template.name : data.name;
                        scope.name_id = data.unified_job_template;
                    }
                    if (data.type === 'project_update') {
                        scope.name_link = "project";
                        scope.name_id = data.unified_job_template;
                    }
                    if (data.type === 'inventory_update') {
                        scope.name_link = "inventory_source";
                        scope.name_id = scope.group;
                    }
                }

                AddTable({ scope: scope, form: LogViewerStatusForm, id: 'status-form-container', getIcon: getIcon });
                AddTable({ scope: scope, form: LogViewerOptionsForm, id: 'options-form-container', getIcon: getIcon });

                if (data.result_stdout) {
                    $('#logview-tabs li:eq(1)').show();
                    AddPreFormattedText({
                        id: 'stdout-form-container',
                        val: data.result_stdout
                    });
                }

                if (data.result_traceback) {
                    $('#logview-tabs li:eq(2)').show();
                    AddPreFormattedText({
                        id: 'traceback-form-container',
                        val: data.result_traceback
                    });
                }

                /*if (data.job_env) {
                    EnvTable({
                        id: 'env-form-container',
                        vars: data.job_env
                    });
                }*/

                if (data.extra_vars) {
                    $('#logview-tabs li:eq(4)').show();
                    AddTextarea({
                        container_id: 'variables-container',
                        fld_id: 'variables',
                        val: ParseVariableString(data.extra_vars)
                    });
                }

                if (data.source_vars) {
                    $('#logview-tabs li:eq(5)').show();
                    AddTextarea({
                        container_id: 'source-container',
                        fld_id: 'source-variables',
                        val: ParseVariableString(data.source_vars)
                    });
                }

                if (!Empty(scope.source)) {
                    if (scope.removeChoicesReady) {
                        scope.removeChoicesReady();
                    }
                    scope.removeChoicesReady = scope.$on('ChoicesReady', function() {
                        scope.source_choices.every(function(e) {
                            if (e.value === scope.source) {
                                scope.source = e.label;
                                return false;
                            }
                            return true;
                        });
                    });
                    GetChoices({
                        scope: scope,
                        url: GetBasePath('inventory_sources'),
                        field: 'source',
                        variable: 'source_choices',
                        choice_name: 'choices',
                        callback: 'ChoicesReady'
                    });
                }

                if (!Empty(scope.credential)) {
                    LookUpName({
                        scope: scope,
                        scope_var: 'credential',
                        url: GetBasePath('credentials') + scope.credential + '/'
                    });
                }

                if (!Empty(scope.inventory)) {
                    LookUpName({
                        scope: scope,
                        scope_var: 'inventory',
                        url: GetBasePath('inventory') + scope.inventory + '/'
                    });
                }

                if (!Empty(scope.project)) {
                    LookUpName({
                        scope: scope,
                        scope_var: 'project',
                        url: GetBasePath('projects') + scope.project + '/'
                    });
                }

                if (!Empty(scope.cloud_credential)) {
                    LookUpName({
                        scope: scope,
                        scope_var: 'cloud_credential',
                        url: GetBasePath('credentials') + scope.cloud_credential + '/'
                    });
                }

                if (!Empty(scope.inventory_source)) {
                    LookUpName({
                        scope: scope,
                        scope_var: 'inventory_source',
                        url: GetBasePath('inventory_sources') + scope.inventory_source + '/'
                    });
                }

                resizeText = function() {
                    var u = $('#logview-tabs').outerHeight() + 25,
                        h = $('#logviewer-modal-dialog').innerHeight(),
                        rows = Math.floor((h - u) / 20);
                    rows -= 3;
                    rows = (rows < 6) ? 6 : rows;
                    $('#logviewer-modal-dialog #variables').attr({ rows: rows });
                    $('#logviewer-modal-dialog #source-variables').attr({ rows: rows });
                };

                elem = angular.element(document.getElementById('logviewer-modal-dialog'));
                $compile(elem)(scope);

                CreateDialog({
                    scope: scope,
                    width: 600,
                    height: 550,
                    minWidth: 450,
                    callback: 'ModalReady',
                    id: 'logviewer-modal-dialog',
                    onResizeStop: resizeText,
                    title: 'Job Results',
                    onOpen: function() {
                        $('#logview-tabs a:first').tab('show');
                        $('#dialog-ok-button').focus();
                        resizeText();
                    }
                });
            });

            GetJob({
                url: url,
                scope: scope
            });

            scope.modalOK = function() {
                $('#logviewer-modal-dialog').dialog('close');
                scope.$destroy();
            };
        };
    }])

    .factory('GetJob', ['Rest', 'ProcessErrors', function(Rest, ProcessErrors) {
        return function(params) {
            var url = params.url,
                scope = params.scope;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data){
                    scope.$emit('JobReady', data);
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('LookUpName', ['Rest', 'ProcessErrors', 'Empty', function(Rest, ProcessErrors, Empty) {
        return function(params) {
            var url = params.url,
                scope_var = params.scope_var,
                scope = params.scope;
            Rest.setUrl(url);
            Rest.get()
                .success(function(data) {
                    if (scope_var === 'inventory_source') {
                        scope[scope_var + '_name'] = data.summary_fields.group.name;
                    }
                    else if (!Empty(data.name)) {
                        scope[scope_var + '_name'] = data.name;
                    }
                    if (!Empty(data.group)) {
                        // Used for inventory_source
                        scope.group = data.group;
                    }
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('AddTable', ['$compile', 'Empty', 'Find', function($compile, Empty, Find) {
        return function(params) {
            var form = params.form,
                id = params.id,
                scope = params.scope,
                getIcon = params.getIcon,
                fld, html, url, e,
                urls = [
                    { "variable": "credential", "url": "/#/credentials/" },
                    { "variable": "project", "url": "/#/projects/" },
                    { "variable": "inventory", "url": "/#/inventories/" },
                    { "variable": "cloud_credential", "url": "/#/credentials/" },
                    { "variable": "inventory_source", "url": "/#/home/groups/?id={{ group }}" },
                    { "variable": "job_template", "url": "/#/job_templates/" },
                    { "variable": "created_by", "url": "/#/users/" }
                ];
            html = "<table class=\"table logviewer-status\">\n";
            for (fld in form.fields) {
                if (!Empty(scope[fld])) {
                    html += "<tr><td class=\"fld-label col-md-3 col-sm-3 col-xs-3\">" + form.fields[fld].label + "</td>" +
                        "<td>";
                    url = Find({ list: urls, key: "variable", val: fld });
                    if (url) {
                        html += "<a href=\"" + url.url;
                        html += (fld === "inventory_source") ? "" : scope[fld];
                        html += "\" ng-click=\"modalOK()\">{{ " + fld + '_name' + " }}</a>";
                    }
                    else if (fld === 'name' && scope.name_link) {
                        url = Find({ list: urls, key: "variable", val: scope.name_link });
                        html += "<a href=\"" + url.url + ( (scope.name_link === 'inventory_source') ? '' : scope.name_id ) + "\" ng-click=\"modalOK()\">{{ " +
                             ( (scope.name_link === 'inventory_source') ? 'inventory_source_name' : fld ) + " }}</a>";
                    }
                    else if (fld === 'elapsed') {
                        html += scope[fld] + " <span class=\"small-text\">seconds</span>";
                    }
                    else if (fld === 'status') {
                        if (getIcon) {
                            html += "<i class=\"fa icon-job-" + getIcon(scope[fld]) + "\"></i> " + scope[fld];
                        }
                        else {
                            html += "<i class=\"fa icon-job-" + scope[fld] + "\"></i> " + scope[fld];
                        }
                        if (scope.job_explanation) {
                            html += "<p style=\"padding-top: 12px\">" + scope.job_explanation + "</p>";
                        }
                    }
                    else {
                        html += "{{ " + fld ;
                        html += (form.fields[fld].filter) ? " | " + form.fields[fld].filter  : "" ;
                        html += " }}";
                    }
                    html += "</td></tr>\n";
                }
            }
            html += "</table>\n";
            e = angular.element(document.getElementById(id));
            e.empty().html(html);
            $compile(e)(scope);
        };
    }])

    .factory('AddTextarea', [ function() {
        return function(params) {
            var container_id = params.container_id,
                val = params.val,
                fld_id = params.fld_id,
                html;
            html = "<div class=\"form-group\">\n" +
                "<textarea id=\"" + fld_id + "\" class=\"form-control mono-space\" rows=\"12\" readonly>" + val + "</textarea>" +
                "</div>\n";
            $('#' + container_id).empty().html(html);
        };
    }])

    .factory('AddPreFormattedText', [function() {
        return function(params) {
            var id = params.id,
                val = params.val,
                html;
            html = "<pre>" + val + "</pre>\n";
            $('#' + id).empty().html(html);
        };
    }])

    .factory('EnvTable', [ function() {
        return function(params) {
            var id = params.id,
                vars = params.vars,
                key, html;
            html = "<table class=\"table logviewer-status\">\n";
            for (key in vars) {
                html += "<tr><td class=\"fld-label col-md-4 col-sm-3 col-xs-3 break\">" + key + "</td>" +
                    "<td class=\"break\">" + vars[key] + "</td></tr>\n";
            }
            html += "</table>\n";
            $('#' + id).empty().html(html);
        };
    }]);