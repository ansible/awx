'use strict';

describe('Service: SocketService', () => {

    let SocketService,
        rootScope,
        event;

    beforeEach(angular.mock.module('shared'));
    beforeEach(angular.mock.module('socket', function($provide){
        $provide.value('$rootScope', rootScope);
        $provide.value('$location', {url: function(){}});
    }));
    beforeEach(angular.mock.inject(($rootScope, _SocketService_) => {
        rootScope = $rootScope.$new();
        rootScope.$emit = jasmine.createSpy('$emit');
        SocketService = _SocketService_;
    }));

    describe('socket onmessage() should broadcast to correct event listener', function(){

        it('should send to ws-jobs-summary', function(){
            event = {data : {group_name: "jobs"}};
            event.data = JSON.stringify(event.data);
            console.log(event);
            SocketService.onMessage(event);
            expect(rootScope.$emit).toHaveBeenCalledWith('ws-jobs-summary', event.data);
        });
    });

});
