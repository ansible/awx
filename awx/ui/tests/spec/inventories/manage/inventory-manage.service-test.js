'use strict';

describe('Service: InventoryManageService', () => {

    let Rest,
        InventoryManageService;

    beforeEach(angular.mock.module('Tower'), ($provide)=>{
        $provide.value('Rest', Rest);
    });
    beforeEach(angular.mock.module('inventoryManage'));
    beforeEach(angular.mock.inject(($httpBackend, _InventoryManageService_) =>{
        Rest = $httpBackend;
        InventoryManageService = _InventoryManageService_;
    }));

    xdescribe('RESTy methods should handle errors', () => {

        beforeEach(() => {
            spyOn(InventoryManageService, 'error');
        });
        it('InventoryManageService.getInventory should handle errors', () => {
            Rest.expectGET('/api/v1/inventory:id/').respond(400, {});
            Rest.flush();
            expect(InventoryManageService.error).toHaveBeenCalled();
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
