/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  LogViewer.js
 *
 */

'use strict';

angular.module('LogViewerHelper', ['ModalDialog', 'Utilities', 'FormGenerator'])

    .factory('LogViewer', ['$compile', 'CreateDialog', 'GetJob', 'Wait', 'GenerateForm', 'LogViewerStatusForm', 'AddTable', 'AddTextarea',
    'LogViewerOptionsForm', 'EnvTable', 'GetBasePath', 'LookUpName', 'Empty',
    function($compile, CreateDialog, GetJob, Wait, GenerateForm, LogViewerStatusForm, AddTable, AddTextarea, LogViewerOptionsForm, EnvTable,
    GetBasePath, LookUpName, Empty) {
        return function(params) {
            var parent_scope = params.scope,
                url = params.url,
                scope = parent_scope.$new();
            
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
                
                for (key in data) {
                    scope[key] = data[key];
                }
                
                AddTable({ scope: scope, form: LogViewerStatusForm, id: 'status-form-container' });
                AddTable({ scope: scope, form: LogViewerOptionsForm, id: 'options-form-container' });
                
                if (data.result_stdout) {
                    AddTextarea({
                        container_id: 'stdout-form-container',
                        val: data.result_stdout,
                        fld_id: 'stdout-textarea'
                    });
                }
                else {
                    $('#logview-tabs li:eq(2)').hide();
                }

                if (data.result_traceback) {
                    AddTextarea({
                        container_id: 'traceback-form-container',
                        val: data.result_traceback,
                        fld_id: 'traceback-textarea'
                    });
                }
                else {
                    $('#logview-tabs li:eq(2)').hide();
                }

                if (data.job_env) {
                    EnvTable({
                        id: 'env-form-container',
                        vars: data.job_env
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
                        url: GetBasePath('inventories') + scope.inventory + '/'
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
                    $('#stdout-textarea').attr({ rows: rows });
                    $('#traceback-textarea').attr({ rows: rows });
                };

                elem = angular.element(document.getElementById('logviewer-modal-dialog'));
                $compile(elem)(scope);

                CreateDialog({
                    scope: scope,
                    width: 600,
                    height: 675,
                    minWidth: 450,
                    callback: 'ModalReady',
                    id: 'logviewer-modal-dialog',
                    onResizeStop: resizeText,
                    onOpen: function() {
                        $('#logview-tabs a:first').tab('show');
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
                    if (!Empty(data.name)) {
                        scope[scope_var] = data.name;
                    }
                })
                .error(function(data, status) {
                    ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                        msg: 'Failed to retrieve ' + url + '. GET returned: ' + status });
                });
        };
    }])

    .factory('AddTable', ['Empty', function(Empty) {
        return function(params) {
            var form = params.form,
                id = params.id,
                scope = params.scope,
                fld, html;
            html = "<table class=\"table logviewer-status\">\n";
            for (fld in form.fields) {
                if (!Empty(scope[fld])) {
                    html += "<tr><td class=\"fld-label col-md-3 col-sm-3 col-xs-3\">" + form.fields[fld].label + "</td>" +
                        "<td>";
                    if (fld === "credential" || fld === "project" || fld === "inventory" || fld === "cloud_credential" ||
                        fld === "inventory_source") {
                        html += "{{ " + fld + " }}";
                    }
                    else {
                        html += scope[fld];
                    }
                    html += "</td></tr>\n";
                }
            }
            html += "</table>\n";
            $('#' + id).empty().html(html);
        };
    }])

    .factory('AddTextarea', [ function() {
        return function(params) {
            var container_id = params.container_id,
                val = params.val,
                fld_id = params.fld_id,
                html;
            html = "<div class=\"form-group\">\n" +
                "<textarea id=\"" + fld_id + "\" class=\"form-control nowrap mono-space\" rows=\"12\" readonly>" + val + "</textarea>" +
                "</div>\n";
            $('#' + container_id).empty().html(html);
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