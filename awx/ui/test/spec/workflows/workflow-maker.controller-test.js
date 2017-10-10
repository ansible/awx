'use strict';

describe('Controller: WorkflowMaker', () => {
    // Setup
    let scope,
        WorkflowMakerController,
        TemplatesService,
        q,
        getWorkflowJobTemplateNodesDeferred;

    beforeEach(angular.mock.module('awApp'));
    beforeEach(angular.mock.module('templates', () => {

        TemplatesService = {
            getWorkflowJobTemplateNodes: function(){
                return angular.noop;
            }
        };

    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, $q) => {
        scope = $rootScope.$new();
        scope.closeDialog = jasmine.createSpy();
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
        scope.workflowJobTemplateObj = {
            id: 1
        };
        q = $q;
        getWorkflowJobTemplateNodesDeferred = q.defer();
        TemplatesService.getWorkflowJobTemplateNodes = jasmine.createSpy('getWorkflowJobTemplateNodes').and.returnValue(getWorkflowJobTemplateNodesDeferred.promise);
        WorkflowMakerController = $controller('WorkflowMakerController', {
            $scope: scope,
            TemplatesService: TemplatesService
        });
    }));

    describe('scope.closeWorkflowMaker()', () => {

        it('should close the dialog', ()=>{
            scope.closeWorkflowMaker();
            expect(scope.closeDialog).toHaveBeenCalled();
        });

    });

});
