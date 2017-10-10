'use strict';

describe('Service: InventoriesService', () => {

    let Rest,
        InventoriesService;

    beforeEach(angular.mock.module('awApp'), ($provide)=>{
        $provide.value('Rest', Rest);
    });
    beforeEach(angular.mock.module('inventoryManage'));
    beforeEach(angular.mock.inject(($httpBackend, _InventoriesService_) =>{
        Rest = $httpBackend;
        InventoriesService = _InventoriesService_;
    }));

    xdescribe('RESTy methods should handle errors', () => {

        beforeEach(() => {
            spyOn(InventoriesService, 'error');
        });
        it('InventoriesService.getInventory should handle errors', () => {
            Rest.expectGET('/api/v2/inventory:id/').respond(400, {});
            Rest.flush();
            expect(InventoriesService.error).toHaveBeenCalled();
        });
    });

    // Unit tests often reveal which pieces of our code should be factored out
    xit('RESTy methods should start/stop spinny', function(){

    });

    afterEach(function() {
        Rest.verifyNoOutstandingExpectation();
        Rest.verifyNoOutstandingRequest();
    });
});
