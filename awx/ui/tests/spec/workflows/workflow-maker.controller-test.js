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
        scope.treeData = {
            data: {
                id: 1,
                canDelete: false,
                canEdit: false,
                canAddTo: true,
                isStartNode: true,
                unifiedJobTemplate: {
                    name: "Workflow Launch"
                },
                children: [],
                deletedNodes: [],
                totalNodes: 0
            },
            nextIndex: 2
        };
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
    
});
