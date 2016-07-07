/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$stateParams', '$scope', '$state', 'Wait', 'JobDetailService', 'hostEvent', 'hostResults',
    function($stateParams, $scope, $state, Wait, JobDetailService, hostEvent, hostResults){

        $scope.processEventStatus = JobDetailService.processEventStatus;
        $scope.hostResults = [];
        // Avoid rendering objects in the details fieldset
        // ng-if="processResults(value)" via host-event-details.partial.html
        $scope.processResults = function(value){
            if (typeof value === 'object'){return false;}
            else {return true;}
        };
        $scope.isStdOut = function(){
            if ($state.current.name === 'jobDetails.host-event.stdout' || $state.current.name === 'jobDetaisl.histe-event.stderr'){
                return 'StandardOut-preContainer StandardOut-preContent';
            }
        };
        /*ignore jslint start*/
        var initCodeMirror = function(el, data, mode){
            var container = document.getElementById(el);
            var editor = CodeMirror.fromTextArea(container, {  // jshint ignore:line
                lineNumbers: true,
                mode: mode
            });
            editor.setSize("100%", 300);
            editor.getDoc().setValue(data);
        };
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
            $scope.event = _.cloneDeep(hostEvent);
            $scope.hostResults = hostResults;
            $scope.json = JobDetailService.processJson(hostEvent);

            // grab standard out & standard error if present, and remove from the results displayed in the details panel
            if (hostEvent.event_data.res.stdout){
                $scope.stdout = hostEvent.event_data.res.stdout;
                delete $scope.event.event_data.res.stdout;
            }
            if (hostEvent.event_data.res.stderr){
                $scope.stderr = hostEvent.event_data.res.stderr;
                delete $scope.event.event_data.res.stderr;
            }
            // instantiate Codemirror
            // try/catch pattern prevents the abstract-state controller from complaining about element being null
            if ($state.current.name === 'jobDetail.host-event.json'){
                try{
                    initCodeMirror('HostEvent-codemirror', JSON.stringify($scope.json, null, 4), {name: "javascript", json: true});
                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            else if ($state.current.name === 'jobDetail.host-event.stdout'){
                try{
                    initCodeMirror('HostEvent-codemirror', $scope.stdout, 'shell');
                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            else if ($state.current.name === 'jobDetail.host-event.stderr'){
                try{
                    initCodeMirror('HostEvent-codemirror', $scope.stderr, 'shell');
                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            $('#HostEvent').modal('show');
        };
        init();
    }];
