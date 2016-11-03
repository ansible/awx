'use strict';

describe('Controller: WorkflowAdd', () => {
    // Setup
    let scope,
        state,
        WorkflowAdd,
        ClearScope,
        Alert,
        GenerateForm,
        initSurvey,
        JobTemplateService,
        q,
        getLabelsDeferred,
        createWorkflowJobTemplateDeferred,
        httpBackend,
        ProcessErrors,
        CreateSelect2,
        Wait,
        ParseTypeChange,
        ToJSON;

    beforeEach(angular.mock.module('Tower'));
    beforeEach(angular.mock.module('jobTemplates', ($provide) => {

        state = jasmine.createSpyObj('state', [
            '$get',
            'transitionTo',
            'go'
        ]);

        GenerateForm = jasmine.createSpyObj('GenerateForm', [
            'inject',
            'reset',
            'clearApiErrors'
        ]);

        JobTemplateService = {
            getLabelOptions: function(){
                return angular.noop;
            },
            createWorkflowJobTemplate: function(){
                return angular.noop;
            }
        };

        ClearScope = jasmine.createSpy('ClearScope');
        Alert = jasmine.createSpy('Alert');
        ProcessErrors = jasmine.createSpy('ProcessErrors');
        CreateSelect2 = jasmine.createSpy('CreateSelect2');
        Wait = jasmine.createSpy('Wait');
        ParseTypeChange = jasmine.createSpy('ParseTypeChange');
        ToJSON = jasmine.createSpy('ToJSON');

        $provide.value('ClearScope', ClearScope);
        $provide.value('Alert', Alert);
        $provide.value('GenerateForm', GenerateForm);
        $provide.value('state', state);
        $provide.value('ProcessErrors', ProcessErrors);
        $provide.value('CreateSelect2', CreateSelect2);
        $provide.value('Wait', Wait);
        $provide.value('ParseTypeChange', ParseTypeChange);
        $provide.value('ToJSON', ToJSON);
    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, $q, $httpBackend, _state_, _ConfigService_, _ClearScope_, _GetChoices_, _Alert_, _GenerateForm_, _ProcessErrors_, _CreateSelect2_, _Wait_, _ParseTypeChange_, _ToJSON_) => {
        scope = $rootScope.$new();
        state = _state_;
        q = $q;
        ClearScope = _ClearScope_;
        Alert = _Alert_;
        GenerateForm = _GenerateForm_;
        httpBackend = $httpBackend;
        ProcessErrors = _ProcessErrors_;
        CreateSelect2 = _CreateSelect2_;
        Wait = _Wait_;
        getLabelsDeferred = q.defer();
        createWorkflowJobTemplateDeferred = q.defer();
        ParseTypeChange = _ParseTypeChange_;
        ToJSON = _ToJSON_;

        JobTemplateService.getLabelOptions = jasmine.createSpy('getLabelOptions').and.returnValue(getLabelsDeferred.promise);
        JobTemplateService.createWorkflowJobTemplate = jasmine.createSpy('createWorkflowJobTemplate').and.returnValue(createWorkflowJobTemplateDeferred.promise);

        WorkflowAdd = $controller('WorkflowAdd', {
            $scope: scope,
            $state: state,
            ClearScope: ClearScope,
            Alert: Alert,
            GenerateForm: GenerateForm,
            JobTemplateService: JobTemplateService,
            ProcessErrors: ProcessErrors,
            CreateSelect2: CreateSelect2,
            Wait: Wait,
            ParseTypeChange: ParseTypeChange,
            ToJSON
        });
    }));

    it('should call ClearScope', ()=>{
        expect(ClearScope).toHaveBeenCalled();
    });

    it('should call GenerateForm.inject', ()=>{
        expect(GenerateForm.inject).toHaveBeenCalled();
    });

    it('should call GenerateForm.reset', ()=>{
        expect(GenerateForm.reset).toHaveBeenCalled();
    });

    it('should get/set the label options and select2-ify the input', ()=>{
        // Resolve JobTemplateService.getLabelsForJobTemplate
        getLabelsDeferred.resolve({
            foo: "bar"
        });
        // We expect the digest cycle to fire off this call to /static/config.js so we go ahead and handle it
        httpBackend.expectGET('/static/config.js').respond(200);
        scope.$digest();
        expect(scope.labelOptions).toEqual({
            foo: "bar"
        });
        expect(CreateSelect2).toHaveBeenCalledWith({
            element:'#workflow_labels',
            multiple: true,
            addNew: true
        });
    });

    it('should call ProcessErrors when getLabelsForJobTemplate returns a rejected promise', ()=>{
        // Reject JobTemplateService.getLabelsForJobTemplate
        getLabelsDeferred.reject({
            data: "mockedData",
            status: 400
        });
        // We expect the digest cycle to fire off this call to /static/config.js so we go ahead and handle it
        httpBackend.expectGET('/static/config.js').respond(200);
        scope.$digest();
        expect(ProcessErrors).toHaveBeenCalled();
    });

    describe('scope.formSave()', () => {

        it('should call JobTemplateService.createWorkflowJobTemplate', ()=>{
            scope.name = "Test Workflow";
            scope.description = "This is a test description";
            scope.formSave();
            expect(JobTemplateService.createWorkflowJobTemplate).toHaveBeenCalledWith({
                name: "Test Workflow",
                description: "This is a test description",
                labels: undefined,
                organization: undefined,
                variables: undefined,
                extra_vars: undefined
            });
        });

    });

    describe('scope.formCancel()', () => {

        it('should transition to templates', ()=>{
            scope.formCancel();
            expect(state.transitionTo).toHaveBeenCalledWith('templates');
        });

    });

});
