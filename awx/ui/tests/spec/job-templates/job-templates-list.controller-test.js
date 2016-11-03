'use strict';

describe('Controller: JobTemplatesList', () => {
    // Setup
    let scope,
        rootScope,
        state,
        JobTemplatesList,
        ClearScope,
        GetChoices,
        Alert,
        Prompt,
        InitiatePlaybookRun,
        rbacUiControlService,
        canAddDeferred,
        q,
        JobTemplateService,
        deleteWorkflowJobTemplateDeferred,
        deleteJobTemplateDeferred;

    beforeEach(angular.mock.module('Tower'));
    beforeEach(angular.mock.module('jobTemplates', ($provide) => {

        state = jasmine.createSpyObj('state', [
            '$get',
            'transitionTo',
            'go'
        ]);

        state.params = {
            id: 1
        };

        rbacUiControlService = {
            canAdd: function(){
                return angular.noop;
            }
        };

        JobTemplateService = {
            deleteWorkflowJobTemplate: function(){
                return angular.noop;
            },
            deleteJobTemplate: function(){
                return angular.noop;
            }
        };

        ClearScope = jasmine.createSpy('ClearScope');
        GetChoices = jasmine.createSpy('GetChoices');
        Alert = jasmine.createSpy('Alert');
        Prompt = jasmine.createSpy('Prompt').and.callFake(function(args) {
            args.action();
        });
        InitiatePlaybookRun = jasmine.createSpy('InitiatePlaybookRun');

        $provide.value('ClearScope', ClearScope);
        $provide.value('GetChoices', GetChoices);
        $provide.value('Alert', Alert);
        $provide.value('Prompt', Prompt);
        $provide.value('state', state);
        $provide.value('InitiatePlaybookRun', InitiatePlaybookRun);
    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, $q, _state_, _ConfigService_, _ClearScope_, _GetChoices_, _Alert_, _Prompt_, _InitiatePlaybookRun_) => {
        scope = $rootScope.$new();
        rootScope = $rootScope;
        q = $q;
        state = _state_;
        ClearScope = _ClearScope_;
        GetChoices = _GetChoices_;
        Alert = _Alert_;
        Prompt = _Prompt_;
        InitiatePlaybookRun = _InitiatePlaybookRun_;
        canAddDeferred = q.defer();
        deleteWorkflowJobTemplateDeferred = q.defer();
        deleteJobTemplateDeferred = q.defer();

        rbacUiControlService.canAdd = jasmine.createSpy('canAdd').and.returnValue(canAddDeferred.promise);

        JobTemplateService.deleteWorkflowJobTemplate = jasmine.createSpy('deleteWorkflowJobTemplate').and.returnValue(deleteWorkflowJobTemplateDeferred.promise);
        JobTemplateService.deleteJobTemplate = jasmine.createSpy('deleteJobTemplate').and.returnValue(deleteJobTemplateDeferred.promise);

        JobTemplatesList = $controller('JobTemplatesList', {
            $scope: scope,
            $rootScope: rootScope,
            $state: state,
            ClearScope: ClearScope,
            GetChoices: GetChoices,
            Alert: Alert,
            Prompt: Prompt,
            InitiatePlaybookRun: InitiatePlaybookRun,
            rbacUiControlService: rbacUiControlService,
            JobTemplateService: JobTemplateService
        });
    }));

    it('should call GetChoices', ()=> {
        expect(GetChoices).toHaveBeenCalled();
    });

    describe('scope.editJobTemplate()', () => {

        it('should call Alert when template param is not present', ()=>{
            scope.editJobTemplate();
            expect(Alert).toHaveBeenCalledWith('Error: Unable to edit template', 'Template parameter is missing');
        });

        it('should transition to templates.editJobTemplate when type is "Job Template"', ()=>{

            var testTemplate = {
                type: "Job Template",
                id: 1
            };

            scope.editJobTemplate(testTemplate);
            expect(state.transitionTo).toHaveBeenCalledWith('templates.editJobTemplate', {id: 1});
        });

        it('should transition to templates.templates.editWorkflowJobTemplate when type is "Workflow Job Template"', ()=>{

            var testTemplate = {
                type: "Workflow Job Template",
                id: 1
            };

            scope.editJobTemplate(testTemplate);
            expect(state.transitionTo).toHaveBeenCalledWith('templates.editWorkflowJobTemplate', {id: 1});
        });

        it('should call Alert when type is not "Job Template" or "Workflow Job Template"', ()=>{

            var testTemplate = {
                type: "Some Other Type",
                id: 1
            };

            scope.editJobTemplate(testTemplate);
            expect(Alert).toHaveBeenCalledWith('Error: Unable to determine template type', 'We were unable to determine this template\'s type while routing to edit.');
        });

    });

    describe('scope.deleteJobTemplate()', () => {

        it('should call Alert when template param is not present', ()=>{
            scope.deleteJobTemplate();
            expect(Alert).toHaveBeenCalledWith('Error: Unable to delete template', 'Template parameter is missing');
        });

        it('should call Prompt if template param is present', ()=>{

            var testTemplate = {
                id: 1,
                name: "Test Template"
            };

            scope.deleteJobTemplate(testTemplate);
            expect(Prompt).toHaveBeenCalled();
        });

        it('should call JobTemplateService.deleteWorkflowJobTemplate when the user takes affirmative action on the delete modal and type = "Workflow Job Template"', ()=>{
            // Note that Prompt has been mocked up above to immediately call the callback function that gets passed in
            // which is how we access the private function in the controller

            var testTemplate = {
                id: 1,
                name: "Test Template",
                type: "Workflow Job Template"
            };

            scope.deleteJobTemplate(testTemplate);
            expect(JobTemplateService.deleteWorkflowJobTemplate).toHaveBeenCalled();
        });

        it('should call JobTemplateService.deleteJobTemplate when the user takes affirmative action on the delete modal and type = "Workflow Job Template"', ()=>{
            // Note that Prompt has been mocked up above to immediately call the callback function that gets passed in
            // which is how we access the private function in the controller

            var testTemplate = {
                id: 1,
                name: "Test Template",
                type: "Job Template"
            };

            scope.deleteJobTemplate(testTemplate);
            expect(JobTemplateService.deleteJobTemplate).toHaveBeenCalled();
        });

    });

    describe('scope.submitJob()', () => {

        it('should call Alert when template param is not present', ()=>{
            scope.submitJob();
            expect(Alert).toHaveBeenCalledWith('Error: Unable to launch template', 'Template parameter is missing');
        });

        it('should call InitiatePlaybookRun when type is "Job Template"', ()=>{

            var testTemplate = {
                type: "Job Template",
                id: 1
            };

            scope.submitJob(testTemplate);
            expect(InitiatePlaybookRun).toHaveBeenCalled();
        });

        xit('should call [something] when type is "Workflow Job Template"', ()=>{

            var testTemplate = {
                type: "Workflow Job Template",
                id: 1
            };

            scope.submitJob(testTemplate);
            expect([something]).toHaveBeenCalled();
        });

        it('should call Alert when type is not "Job Template" or "Workflow Job Template"', ()=>{

            var testTemplate = {
                type: "Some Other Type",
                id: 1
            };

            scope.submitJob(testTemplate);
            expect(Alert).toHaveBeenCalledWith('Error: Unable to determine template type', 'We were unable to determine this template\'s type while launching.');
        });

    });

    describe('scope.scheduleJob()', () => {

        it('should transition to jobTemplateSchedules when type is "Job Template"', ()=>{

            var testTemplate = {
                type: "Job Template",
                id: 1
            };

            scope.scheduleJob(testTemplate);
            expect(state.go).toHaveBeenCalledWith('jobTemplateSchedules', {id: 1});
        });

        it('should transition to workflowJobTemplateSchedules when type is "Workflow Job Template"', ()=>{

            var testTemplate = {
                type: "Workflow Job Template",
                id: 1
            };

            scope.scheduleJob(testTemplate);
            expect(state.go).toHaveBeenCalledWith('workflowJobTemplateSchedules', {id: 1});
        });

        it('should call Alert when template param is not present', ()=>{
            scope.scheduleJob();
            expect(Alert).toHaveBeenCalledWith('Error: Unable to schedule job', 'Template parameter is missing');
        });

    });

});
