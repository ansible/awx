describe('View: Split Jobs List', () => {
    let JobList,
        scope,
        state,
        Dataset,
        resolvedModels,
        JobsStrings,
        QuerySet,
        Prompt,
        filter,
        ProcessErrors,
        Wait,
        Rest,
        SearchBasePath;

    beforeEach(angular.mock.module('at.features.jobs', ($provide) => {
        Dataset = {
            data: {
                results: {}
            }
        }
        state = {
            params: {
                job_search: {}
            },
            go: jasmine.createSpy('go'),
            includes: jasmine.createSpy('includes')
        }
        resolvedModels = [
            {
                options: () => {
                    return ["foo", "bar"];
                }
            }
        ]

        ProcessErrors = jasmine.createSpy('ProcessErrors');
        Wait = jasmine.createSpy('Wait');
        Prompt = jasmine.createSpy('Prompt');

        $provide.value('state', state);
        $provide.value('Dataset', Dataset);
        $provide.value('resolvedModels', resolvedModels);
        $provide.value('ProcessErrors', ProcessErrors);
        $provide.value('Wait', Wait);
        $provide.value('Prompt', Prompt);
        $provide.value('Rest', angular.noop);
        $provide.value('SearchBasePath', '');
        $provide.value('JobsStrings', angular.noop);
        $provide.value('QuerySet', angular.noop);

        $provide.provider('$stateProvider', { '$get': function() { return function() {}; } });
        $provide.value('$stateExtender', { addState: jasmine.createSpy('addState'), });
    }));

    beforeEach(angular.mock.inject(function($controller, $rootScope, _state_, _Dataset_, _resolvedModels_, _JobsStrings_, _QuerySet_, _Prompt_, _$filter_, _ProcessErrors_, _Wait_, _Rest_, _SearchBasePath_){
        scope = $rootScope.$new();
        state = _state_;
        Dataset = _Dataset_;
        resolvedModels = _resolvedModels_;
        JobsStrings = _JobsStrings_;
        QuerySet = _QuerySet_;
        Prompt = _Prompt_;
        filter = _$filter_;
        ProcessErrors = _ProcessErrors_;
        Wait = _Wait_;
        Rest = _Rest_;
        SearchBasePath = _SearchBasePath_;

        JobList = $controller('jobsListController', {
            $scope: scope,
            $state: state,
            Dataset: Dataset,
            resolvedModels: resolvedModels,
            JobsStrings: JobsStrings,
            ProcessErrors: ProcessErrors,
            QuerySet: QuerySet,
            Wait: Wait,
            Prompt: Prompt,
            $filter: filter,
            Wait: Wait,
            Rest: Rest,
            SearchBasePath: SearchBasePath,
        });
    }));

    describe('JobList Controller', () => {
        it('is created successfully', () => {
            expect(JobList).toBeDefined();
        });
        it('has method "getSplitJobDetails"', () => {
            expect(JobList.getSplitJobDetails).toBeDefined();
        });
        it('returns a string', () => {
            let data = {
                shard: {
                    offset: 1,
                    step: 2
                }
            }
            const result = JobList.getSplitJobDetails(data);
            expect(result).toEqual('Split Job 2/2');
        });
        it('returns null when there is no data', () => {
            let data = undefined;
            const result = JobList.getSplitJobDetails(data);
            expect(result).toBeNull();
        });
        it('returns null when there is no "shard" attribute', () => {
            let data = {
                foo: {}
            };
            const result = JobList.getSplitJobDetails(data);
            expect(result).toBeNull();
        });
        it('returns null when "shard" is an empty object', () => {
            let data = {
                shard: {}
            };
            const result = JobList.getSplitJobDetails(data);
            expect(result).toBeNull();
        });
    });
});