/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

// import detailsController from './details.controller';

const templateUrl = require('~network-ui/zoom-widget/zoom.partial.html');

export default [
    function() {
    return {
        templateUrl,
        restrict: 'E',
        link(scope){

            function init() {
                scope.zoom = 100;
                $( "#networking-slider" ).slider({
                    value:100,
                    min: 0,
                    max: 200,
                    step: 10,
                    slide: function( event, ui ) {
                        scope.zoom = ui.value;
                        scope.zoomTo();
                    }
                });
            }

            init();

            scope.$parent.$on('awxNet-UpdateZoomWidget', (e, scale, updateBoolean) => {
                if(scale && updateBoolean){
                    // scale is included, meaning this was triggered by
                    // the view FSM's onMouseWheel transition
                    let sliderPercent = 40 * (Math.log10(scale) + 3);
                    scope.zoom = Math.round(sliderPercent / 10) * 10;
                }
                $("#networking-slider").slider('value', scope.zoom);
            });

            scope.zoomTo = function() {
                scope.zoom = Math.ceil(scope.zoom / 10) * 10;
                this.$parent.$broadcast('zoom', scope.zoom);
            };

            scope.zoomOut = function(){
                scope.zoom = scope.zoom - 10 > 0 ? scope.zoom - 10 : 0;
                this.$parent.$broadcast('zoom', scope.zoom);
            };

            scope.zoomIn = function(){
                scope.zoom = scope.zoom + 10 < 200 ? scope.zoom + 10 : 200;
                this.$parent.$broadcast('zoom', scope.zoom);
            };
        }
    };
}];
