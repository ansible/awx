'use strict';

describe('Controller: WorkflowMaker', () => {
    // Setup
    let scope,
        WorkflowMakerController,
        WorkflowHelpService;

    beforeEach(angular.mock.module('Tower'));
    beforeEach(angular.mock.module('jobTemplates', ($provide) => {

        WorkflowHelpService = jasmine.createSpyObj('WorkflowHelpService', [
            'closeDialog',
            'addPlaceholderNode',
            'getSiblingConnectionTypes'
        ]);

        $provide.value('WorkflowHelpService', WorkflowHelpService);

    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, _WorkflowHelpService_) => {
        scope = $rootScope.$new();
        WorkflowHelpService = _WorkflowHelpService_;

        WorkflowMakerController = $controller('WorkflowMakerController', {
            $scope: scope,
            WorkflowHelpService: WorkflowHelpService
        });

    }));

    describe('scope.saveWorkflowMaker()', () => {

        it('should close the dialog', ()=>{
            scope.saveWorkflowMaker();
            expect(WorkflowHelpService.closeDialog).toHaveBeenCalled();
        });

    });

    describe('scope.startAddNode()', () => {
        
    });

    describe('scope.confirmNodeForm()', () => {

    });

    describe('scope.cancelNodeForm()', () => {

    });

    describe('scope.startEditNode()', () => {

    });

    describe('scope.startDeleteNode()', () => {

    });

    describe('scope.cancelDeleteNode()', () => {

    });

    describe('scope.confirmDeleteNode()', () => {

    });

    describe('scope.toggleFormTab()', () => {

    });

    describe('scope.toggle_job_template()', () => {

    });

    describe('scope.toggle_project()', () => {

    });

    describe('scope.toggle_inventory_source()', () => {

    });
});
