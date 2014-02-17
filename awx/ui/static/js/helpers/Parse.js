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