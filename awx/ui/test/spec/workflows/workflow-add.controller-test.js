'use strict';

describe('Controller: WorkflowAdd', () => {
    // Setup
    let scope,
        state,
        WorkflowAdd,
        Alert,
        GenerateForm,
        TemplatesService,
        q,
        createWorkflowJobTemplateDeferred,
        httpBackend,
        ProcessErrors,
        CreateSelect2,
        Wait,
        ParseTypeChange,
        ToJSON,
        availableLabels,
        resolvedModels;

    beforeEach(angular.mock.module('awApp'));
    beforeEach(angular.mock.module('RestServices'));
    beforeEach(angular.mock.module('templates', ($provide) => {

        state = jasmine.createSpyObj('state', [
            '$get',
            'transitionTo',
            'go'
        ]);

        GenerateForm = jasmine.createSpyObj('GenerateForm', [
            'inject',
            'reset',
            'clearApiErrors',
            'applyDefaults'
        ]);

        TemplatesService = {
            getLabelOptions: function(){
                return angular.noop;
            },
            createWorkflowJobTemplate: function(){
                return angular.noop;
            }
        };

        availableLabels = [{
            name: "foo",
            id: "1"
        }];

        resolvedModels = [
            {},
            {
                options: () => {
                    return true;
                }
            }
        ];

        Alert = jasmine.createSpy('Alert');
        ProcessErrors = jasmine.createSpy('ProcessErrors');
        CreateSelect2 = jasmine.createSpy('CreateSelect2');
        Wait = jasmine.createSpy('Wait');
        ParseTypeChange = jasmine.createSpy('ParseTypeChange');
        ToJSON = jasmine.createSpy('ToJSON');

        $provide.value('Alert', Alert);
        $provide.value('GenerateForm', GenerateForm);
        $provide.value('state', state);
        $provide.value('ProcessErrors', ProcessErrors);
        $provide.value('CreateSelect2', CreateSelect2);
        $provide.value('Wait', Wait);
        $provide.value('ParseTypeChange', ParseTypeChange);
        $provide.value('ToJSON', ToJSON);
        $provide.value('availableLabels', availableLabels);
        $provide.value('resolvedModels', resolvedModels);
    }));

    beforeEach(angular.mock.inject( ($rootScope, $controller, $q, $httpBackend, _state_, _ConfigService_, _GetChoices_, _Alert_, _GenerateForm_, _ProcessErrors_, _CreateSelect2_, _Wait_, _ParseTypeChange_, _ToJSON_, _availableLabels_) => {
        scope = $rootScope.$new();
        state = _state_;
        q = $q;
        Alert = _Alert_;
        GenerateForm = _GenerateForm_;
        httpBackend = $httpBackend;
        ProcessErrors = _ProcessErrors_;
        CreateSelect2 = _CreateSelect2_;
        Wait = _Wait_;
        createWorkflowJobTemplateDeferred = q.defer();
        ParseTypeChange = _ParseTypeChange_;
        ToJSON = _ToJSON_;
        availableLabels = _availableLabels_;

        $httpBackend
            .whenGET(/^\/api\/?$/)
            .respond(200, '');

        $httpBackend
            .when('OPTIONS', '/')
            .respond(200, '');

        $httpBackend
            .whenGET(/\/static\/*/)
            .respond(200, {});

        TemplatesService.createWorkflowJobTemplate = jasmine.createSpy('createWorkflowJobTemplate').and.returnValue(createWorkflowJobTemplateDeferred.promise);

        WorkflowAdd = $controller('WorkflowAdd', {
            $scope: scope,
            $state: state,
            Alert: Alert,
            GenerateForm: GenerateForm,
            TemplatesService: TemplatesService,
            ProcessErrors: ProcessErrors,
            CreateSelect2: CreateSelect2,
            Wait: Wait,
            ParseTypeChange: ParseTypeChange,
            availableLabels: availableLabels,
            ToJSON
        });
    }));

    it('should get/set the label options and select2-ify the input', ()=>{
        // We expect the digest cycle to fire off this call to /static/config.js so we go ahead and handle it
        httpBackend.expectGET('/static/config.js').respond(200);
        scope.$digest();
        expect(scope.labelOptions).toEqual([{
            label: "foo",
            value: "1"
        }]);
        expect(CreateSelect2).toHaveBeenCalledWith({
            element:'#workflow_job_template_labels',
            multiple: true,
            addNew: true
        });
    });

    describe('scope.formSave()', () => {

        it('should call TemplatesService.createWorkflowJobTemplate', ()=>{
            scope.name = "Test Workflow";
            scope.description = "This is a test description";
            scope.formSave();
            expect(TemplatesService.createWorkflowJobTemplate).toHaveBeenCalledWith({
                name: "Test Workflow",
                description: "This is a test description",
                organization: undefined,
                inventory: undefined,
                limit: undefined,
                scm_branch: undefined,
                labels: undefined,
                variables: undefined,
                allow_simultaneous: undefined,
                webhook_service: '',
                webhook_credential: null,
                ask_inventory_on_launch: false,
                ask_variables_on_launch: false,
                ask_limit_on_launch: false,
                ask_scm_branch_on_launch: false,
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
