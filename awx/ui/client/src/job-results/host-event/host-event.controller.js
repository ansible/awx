/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$stateParams', '$scope', '$state', 'Wait', 'JobDetailService', 'hostEvent', 'hostResults', 'parseStdoutService',
    function($stateParams, $scope, $state, Wait, JobDetailService, hostEvent, hostResults, parseStdoutService){

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
            $scope.json = JobDetailService.processJson(hostEvent);

            // grab standard out & standard error if present, and remove from the results displayed in the details panel
            if (hostEvent.stdout){
                $scope.stdout = parseStdoutService.prettify(hostEvent.stdout);
                delete $scope.event.stdout;
            }
            if (hostEvent.stderr){
                $scope.stderr = hostEvent.stderr;
                delete $scope.event.stderr;
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
