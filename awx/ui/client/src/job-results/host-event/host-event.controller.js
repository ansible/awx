/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$scope', '$state', 'jobResultsService', 'hostEvent',
    function($scope, $state, jobResultsService, hostEvent){

        $scope.processEventStatus = jobResultsService.processEventStatus;
        $scope.processResults = function(value){
            if (typeof value === 'object'){return false;}
            else {return true;}
        };

        var initCodeMirror = function(el, data, mode){
            var container = document.getElementById(el);
            var editor = CodeMirror.fromTextArea(container, {  // jshint ignore:line
                lineNumbers: true,
                mode: mode,
                readOnly: true,
                scrollbarStyle: null
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

        $scope.closeHostEvent = function() {
            // Unbind the listener so it doesn't fire when we close the modal via navigation
            $('#HostEvent').off('hidden.bs.modal');
            $('#HostEvent').modal('hide');
            $state.go('jobResult');
        };

        var init = function(){
            hostEvent.event_name = hostEvent.event;
            $scope.event = _.cloneDeep(hostEvent);

            // grab standard out & standard error if present from the host
            // event's "res" object, for things like Ansible modules. Small
            // wrinkle in this implementation is that the stdout/stderr tabs
            // should be shown if the `res` object has stdout/stderr keys, even
            // if they're a blank string. The presence of these keys is
            // potentially significant to a user.
            try{
                $scope.module_name = hostEvent.event_data.task_action ||  "No result found";
                $scope.stdout = hostEvent.event_data.res.stdout ? hostEvent.event_data.res.stdout : hostEvent.event_data.res.stdout === "" ? " " : undefined;
                $scope.stderr = hostEvent.event_data.res.stderr ? hostEvent.event_data.res.stderr : hostEvent.event_data.res.stderr === "" ? " " : undefined;
                $scope.json = hostEvent.event_data.res;
            }
            catch(err){
                // do nothing, no stdout/stderr for this module
            }
            if($scope.module_name === "debug" &&
                _.has(hostEvent.event_data, "res.result.stdout")){
                    $scope.stdout = hostEvent.event_data.res.result.stdout;
            }
            if($scope.module_name === "yum" &&
                _.has(hostEvent.event_data, "res.results") &&
                _.isArray(hostEvent.event_data.res.results)){
                    $scope.stdout = hostEvent.event_data.res.results[0];
            }
            // instantiate Codemirror
            // try/catch pattern prevents the abstract-state controller from complaining about element being null
            if ($state.current.name === 'jobResult.host-event.json'){
                try{
                    if(_.has(hostEvent.event_data, "res")){
                        initCodeMirror('HostEvent-codemirror', JSON.stringify($scope.json, null, 4), {name: "javascript", json: true});
                        resize();
                    }
                    else{
                        $scope.no_json = true;
                    }

                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            else if ($state.current.name === 'jobResult.host-event.stdout'){
                try{
                    resize();
                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            else if ($state.current.name === 'jobResult.host-event.stderr'){
                try{
                    resize();
                }
                catch(err){
                    // element with id HostEvent-codemirror is not the view controlled by this instance of HostEventController
                }
            }
            $('#HostEvent').modal('show');
            $('.modal-content').resizable({
                minHeight: 523,
                minWidth: 600
            });
            $('.modal-dialog').draggable({
                cancel: '.CodeMirror'
            });

            function resize(){
                if ($state.current.name === 'jobResult.host-event.json'){
                    let editor = $('.CodeMirror')[0].CodeMirror;
                    let height = $('.modal-dialog').height() - $('.HostEvent-header').height() - $('.HostEvent-details').height() - $('.HostEvent-nav').height() - $('.HostEvent-controls').height() - 120;
                    editor.setSize("100%", height);
                }
                else if($state.current.name === 'jobResult.host-event.stdout' || $state.current.name === 'jobResult.host-event.stderr'){
                    let height = $('.modal-dialog').height() - $('.HostEvent-header').height() - $('.HostEvent-details').height() - $('.HostEvent-nav').height() - $('.HostEvent-controls').height() - 120;
                    $(".HostEvent-stdout").width("100%");
                    $(".HostEvent-stdout").height(height);
                    $(".HostEvent-stdoutContainer").height(height);
                    $(".HostEvent-numberColumnPreload").height(height);
                }

            }

            $('.modal-dialog').on('resize', function(){
                resize();
            });

            $('#HostEvent').on('hidden.bs.modal', function () {
                $scope.closeHostEvent();
            });
        };
        init();
    }];
