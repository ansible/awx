/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['templateUrl',
    function(templateUrl) {
        return {
            scope: {
                panChart: '&',
                resetChart: '&',
                zoomChart: '&'
            },
            templateUrl: templateUrl('templates/workflows/workflow-controls/workflow-controls'),
            restrict: 'E',
            link: function(scope) {

                function init() {
                    scope.zoom = 100;
                    $( "#slider" ).slider({
                        value:100,
                        min: 50,
                        max: 200,
                        step: 10,
                        slide: function( event, ui ) {
                            scope.zoom = ui.value;
                            scope.zoomChart({
                                zoom: scope.zoom
                            });
                        }
                    });
                }

                scope.pan = function(direction) {
                    scope.panChart({
                        direction: direction
                    });
                };

                scope.reset = function() {
                    scope.zoom = 100;
                    $("#slider").slider('value',scope.zoom);
                    scope.resetChart();
                };

                scope.zoomIn = function() {
                    scope.zoom = Math.ceil((scope.zoom + 10) / 10) * 10 < 200 ? Math.ceil((scope.zoom + 10) / 10) * 10 : 200;
                    $("#slider").slider('value',scope.zoom);
                    scope.zoomChart({
                        zoom: scope.zoom
                    });
                };

                scope.zoomOut = function() {
                    scope.zoom = Math.floor((scope.zoom - 10) / 10) * 10 > 50 ? Math.floor((scope.zoom - 10) / 10) * 10 : 50;
                    $("#slider").slider('value',scope.zoom);
                    scope.zoomChart({
                        zoom: scope.zoom
                    });
                };

                scope.$on('workflowZoomed', function(evt, params) {
                    scope.zoom = Math.round(params.zoom * 10) * 10;
                    $("#slider").slider('value',scope.zoom);
                });

                init();
            }
        };
    }
];
