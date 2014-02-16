/*********************************************
 *  Copyright (c) 2014 AnsibleWorks, Inc.
 *
 *  ParseHelper
 *
 *  Routines for parsing variable data and toggling
 *  between JSON and YAML.
 *
 */

'use strict';

angular.module('ParseHelper', ['Utilities', 'AngularCodeMirrorModule'])
    .factory('ParseTypeChange', ['Alert', 'AngularCodeMirror', function (Alert, AngularCodeMirror) {
        return function (scope, varName, parseTypeName) {

            // Toggle displayed variable string between JSON and YAML

            var fld = (varName) ? varName : 'variables',
                pfld = (parseTypeName) ? parseTypeName : 'parseType',
                codeMirror = AngularCodeMirror();
            codeMirror.addModes($AnsibleConfig.variable_edit_modes);

            /*
            scope.blockParseTypeWatch = false;
            scope.blockVariableDataWatch = false;

            if (scope['remove' + fld + 'Watch']) {
                scope['remove' + fld + 'Watch']();
            }
            scope['remove' + fld + 'Watch'] = scope.$watch(pfld, function (newVal, oldVal) {
                var json_obj;
                if (newVal !== oldVal) {
                    if (newVal === 'json') {
                        if (scope[fld] && !/^---$/.test(scope[fld])) {
                            // convert YAML to JSON
                            try {
                                json_obj = jsyaml.load(scope[fld]); //parse yaml into an obj
                                scope[fld] = JSON.stringify(json_obj, null, " ");
                            } catch (err) {
                                // ignore parse errors. allow the user to paste values in and sync the
                                // radio button later. parse errors will be flagged on save.
                            }
                        } else {
                            scope[fld] = "{}";
                        }
                    } else {
                        if (scope[fld] && !/^\{\}$/.test(scope[fld])) {
                            // convert JSON to YAML
                            try {
                                json_obj = JSON.parse(scope[fld]);
                                scope[fld] = jsyaml.safeDump(json_obj);
                            } catch (err) {
                                // ignore the errors. allow the user to paste values in and sync the
                                // radio button later. parse errors will be flagged on save.
                            }
                        } else {
                            scope[fld] = "---";
                        }
                    }
                }
            });
            */

            scope.showCodeEditor = function() {
                var title = 'Edit ' + scope[pfld].toUpperCase(),
                    container = document.getElementById('main-view');
                codeMirror.show({
                    scope: scope,
                    container: container,
                    mode: scope[pfld],
                    model: fld,
                    title: title
                });
            };

            scope.parseTypeChange = function() {
                var json_obj;
                if (scope[pfld] === 'json') {
                    // converting yaml to json
                    try {
                        json_obj = jsyaml.load(scope[fld]);
                        if ($.isEmptyObject(json_obj)) {
                            scope[fld] = "{}";
                        }
                        else {
                            scope[fld] = JSON.stringify(json_obj, null, " ");
                        }
                    }
                    catch (e) {
                        Alert('Parse Error', 'Failed to parse valid YAML. ' + e.message);
                        setTimeout( function() { scope.$apply( function() { scope[pfld] = 'yaml'; }); }, 500);
                    }
                }
                else {
                    // convert json to yaml
                    try {
                        json_obj = JSON.parse(scope[fld]);
                        if ($.isEmptyObject(json_obj)) {
                            scope[fld] = '---';
                        }
                        else {
                            scope[fld] = jsyaml.safeDump(json_obj);
                        }
                    }
                    catch (e) {
                        Alert('Parse Error', 'Failed to parse valid JSON. ' + e.message);
                        setTimeout( function() { scope.$apply( function() { scope[pfld] = 'json'; }); }, 500 );
                    }
                }
            };
        };
    }
]);