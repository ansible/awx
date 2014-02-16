/**********************************************
 * sampleApp.js
 *
 * Copyright (c) 2013-2014 Chris Houseknecht
 *
 * Distributed under The MIT License (MIT)
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 *
 */

'use strict';

angular.module('sampleApp', ['ngRoute', 'AngularCodeMirrorModule'])
    
    .config(['$routeProvider', function($routeProvider) {
        $routeProvider
        .when('/', {
            templateUrl: 'partials/main.html',
            controller: 'sampleController'
        })
        .otherwise({
            redirectTo: '/'
        });
    }])

    .controller('sampleController', ['$scope', 'AngularCodeMirror', function($scope, AngularCodeMirror) {

        $scope.parseType = 'json';
        $scope.codeValue = '{}';
        
        var container = document.getElementById('main-view'),
            modes = {
                yaml: {
                    mode:"text/x-yaml",
                    matchBrackets: true,
                    autoCloseBrackets: true,
                    styleActiveLine: true,
                    lineNumbers: true,
                    gutters: ["CodeMirror-lint-markers"],
                    lint: true
                },
                json: {
                    mode: "application/json",
                    styleActiveLine: true,
                    matchBrackets: true,
                    autoCloseBrackets: true,
                    lineNumbers: true,
                    gutters: ["CodeMirror-lint-markers"],
                    lint: true
                }
            },
            codeMirror = AngularCodeMirror();

        codeMirror.addModes(modes);

        $scope.parseTypeChange = function() {
            var json_obj;
            if ($scope.parseType === 'json') {
                // converting yaml to json
                try {
                    json_obj = jsyaml.load($scope.codeValue);
                    if ($.isEmptyObject(json_obj)) {
                        $scope.codeValue = "{}";
                    }
                    else {
                        $scope.codeValue = JSON.stringify(json_obj, null, " ");
                    }
                }
                catch (e) {
                    alert('Failed to parse valid YAML. ' + e.message);
                    setTimeout( function() { $scope.$apply( function() { $scope.parseType = 'yaml'; }); }, 500);
                }
            }
            else {
                // convert json to yaml
                try {
                    json_obj = JSON.parse($scope.codeValue);
                    if ($.isEmptyObject(json_obj)) {
                        $scope.codeValue = '---';
                    }
                    else {
                        $scope.codeValue = jsyaml.safeDump(json_obj);
                    }
                }
                catch (e) {
                    alert('Failed to parse valid JSON. ' + e.message);
                    setTimeout( function() { $scope.$apply( function() { $scope.parseType = 'json'; }); }, 500 );
                }
            }
        };

        $scope.showCodeEditor = function() {
            var title = 'Edit ' + $scope.parseType.toUpperCase();
            codeMirror.show({
                scope: $scope,
                container: container,
                mode: $scope.parseType,
                model: 'codeValue',
                title: title
            });
        };
    
    }])

    .directive('afTooltip', [ function() {
        return {
            link: function(scope, element, attrs) {
                var placement = (attrs.placement) ? attrs.placement : 'top';
                $(element).tooltip({
                    html: true,
                    placement: placement,
                    title: attrs.afTooltip,
                    trigger: 'hover',
                    container: 'body'
                });
            }
        };
    }]);
