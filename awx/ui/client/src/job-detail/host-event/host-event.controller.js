/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/


 export default
    ['$stateParams', '$scope', '$state', 'Wait', 'JobDetailService', 'moment', 'event',
    function($stateParams, $scope, $state, Wait, JobDetailService, moment, event){

        $scope.processEventStatus = JobDetailService.processEventStatus;
        // Avoid rendering objects in the details fieldset
        // ng-if="processResults(value)" via host-event-details.partial.html
        $scope.processResults = function(value){
            if (typeof value == 'object'){return false;}
            else {return true;}
        };

        var codeMirror = function(el, json){
            var el = $(el)[0];
            var editor = CodeMirror.fromTextArea(el, {
                lineNumbers: true,
                mode: {name: "javascript", json: true}
             });
             editor.getDoc().setValue(JSON.stringify(json, null, 4));        
        };

        $scope.getActiveHostIndex = function(){
            var result = $scope.hostResults.filter(function( obj ) {
                return obj.id == $scope.event.id;
            });
            return $scope.hostResults.indexOf(result[0]);
        };

        $scope.showPrev = function(){
            return $scope.getActiveHostIndex() != 0;
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
            console.log(event)
            $scope.event = event.data.results[0];
            $scope.event.created = moment($scope.event.created).format();
            $scope.hostResults = $stateParams.hostResults;
            $scope.json = JobDetailService.processJson($scope.event);
            if ($state.current.name == 'jobDetail.host-event.json'){
                codeMirror('#HostEvent-json', $scope.json);
            }
            try {
                $scope.stdout = JobDetailService.processJson($scope.event.event_data.res)
                console.log($scope.stdout)
                if ($state.current.name == 'jobDetail.host-event.stdout'){
                codeMirror('#HostEvent-stdout', $scope.stdout);
                }
            }
            catch(err){
                $scope.sdout = null;
            }
            console.log($scope)

            
            $('#HostEvent').modal('show');
        };
        init();
    }];