/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$stateParams', '$scope', '$state', 'Wait', 'JobDetailService', 'hostEvent',
    function($stateParams, $scope, $state, Wait, JobDetailService, hostEvent){

        $scope.processEventStatus = JobDetailService.processEventStatus;
        $scope.hostResults = [];
        // Avoid rendering objects in the details fieldset
        // ng-if="processResults(value)" via host-event-details.partial.html
        $scope.processResults = function(value){
            if (typeof value === 'object'){return false;}
            else {return true;}
        };
        /*ignore jslint start*/
        /* jshint ignore:start */
        var initCodeMirror = function(el, json){
            var container = $(el)[0];
            var editor = CodeMirror.fromTextArea(container, {
                lineNumbers: true,
                mode: {name: "javascript", json: true}
            });
            editor.setSize("100%", 300);
            editor.getDoc().setValue(JSON.stringify(json, null, 4));
        };
        /* jshint ignore:end */
        /*ignore jslint end*/
        $scope.isActiveState = function(name){
            return $state.current.name === name;
        };

        $scope.getActiveHostIndex = function(){
            var result = $scope.hostResults.filter(function( obj ) {
                return obj.id === $scope.event.id;
            });
            return $scope.hostResults.indexOf(result[0]);
        };

        $scope.showPrev = function(){
            return $scope.getActiveHostIndex() !== 0;
        };

        $scope.showNext = function(){
            return $scope.getActiveHostIndex() < $scope.hostResults.indexOf($scope.hostResults[$scope.hostResults.length - 1]);
        };

        $scope.goNext = function(){
            var index = $scope.getActiveHostIndex() + 1;
            var id = $scope.hostResults[index].id;
            $state.go('jobDetail.host-event.details', {eventId: id});
        };

        $scope.goPrev = function(){
            var index = $scope.getActiveHostIndex() - 1;
            var id = $scope.hostResults[index].id;
            $state.go('jobDetail.host-event.details', {eventId: id});
        };

        var init = function(){
            $scope.event = hostEvent;
            JobDetailService.getJobEventChildren($stateParams.taskId).success(function(res){
                $scope.hostResults = res.results;
            });
            $scope.json = JobDetailService.processJson($scope.event);
            /* jshint ignore:start */
            if ($state.current.name === 'jobDetail.host-event.json'){
                initCodeMirror('#HostEvent-json', $scope.json);
            }
            try {
                $scope.stdout = JobDetailService
                    .processJson($scope.event.event_data.res.stdout);
                if ($state.current.name === 'jobDetail.host-event.stdout'){
                initCodeMirror('#HostEvent-stdout', $scope.stdout);
                }
            }
            catch(err){
                $scope.stdout = null;
            }
            /* jshint ignore:end */
            $('#HostEvent').modal('show');
        };
        init();
    }];
