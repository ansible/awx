/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$stateParams', '$scope', '$state', 'Wait', 'jobResultsService', 'hostEvent', 'hostResults',
    function($stateParams, $scope, $state, Wait, jobResultsService, hostEvent, hostResults){

        $scope.processEventStatus = jobResultsService.processEventStatus;
        $scope.hostResults = [];
        // Avoid rendering objects in the details fieldset
        // ng-if="processResults(value)" via host-event-details.partial.html
        $scope.processResults = function(value){
            if (typeof value === 'object'){return false;}
            else {return true;}
        };
        $scope.isStdOut = function(){
            if ($state.current.name === 'jobDetail.host-event.stdout' || $state.current.name === 'jobDetail.host-event.stderr'){
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
            editor.setSize("100%", 200);
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

        var init = function(){
            hostEvent.event_name = hostEvent.event;
            $scope.event = _.cloneDeep(hostEvent);
            $scope.hostResults = hostResults;

            // grab standard out & standard error if present from the host
            // event's "res" object, for things like Ansible modules
            try{
                $scope.module_name = hostEvent.event_data.res.invocation.module_name || hostEvent.event_data.task_action || "No result found";
                $scope.stdout = hostEvent.event_data.res.stdout;
                $scope.stderr = hostEvent.event_data.res.stderr;
                $scope.json = hostEvent.event_data.res;
            }
            catch(err){
                // do nothing, no stdout/stderr for this module
            }
            if($scope.module_name === "debug" &&
                hostEvent.event_data.res.hasOwnProperty('result') &&
                hostEvent.event_data.res.result.hasOwnProperty('stdout')){
                    $scope.stdout = hostEvent.event_data.res.result.stdout;
            }
            if($scope.module_name === "yum" &&
                hostEvent.event_data.res.hasOwnProperty('results') &&
                _.isArray(hostEvent.event_data.res.results)){
                    $scope.stdout = hostEvent.event_data.res.results[0];
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
