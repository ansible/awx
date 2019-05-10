'use strict';

const mockUrl = '';
const mockSavedInstanceGroups = {
    data: {
        results: [
            { id: 1 },
            { id: 2 },
            { id: 3 },
            { id: 4 },
            { id: 5 },
            { id: 6 },
        ]
    }
};

const _postData = [];
function MockRest() {
    return {
        setUrl (){},
        get () {
            return Promise.resolve(mockSavedInstanceGroups);
        },
        post (data) {
            _postData.push(data);
            return Promise.resolve({});    
        },
    }
}

describe('instanceGroupsService', () => {
    let instanceGroupsService;

    beforeEach(() => {
        angular.mock.module('awApp');
        angular.mock.module($provide => {
            $provide.service('Rest', MockRest);
        });
        angular.mock.module('instanceGroups');
        angular.mock.inject($injector => {
            instanceGroupsService = $injector.get('InstanceGroupsService');
        });
    });

    describe('editInstanceGroups', () => {
        it('makes the expected requests', (done) => {
            const selectedInstanceGroups = [
                { id: 1 },
                { id: 2 },
                { id: 4 },
                { id: 5 },
                { id: 6 },
                { id: 7 },
                { id: 3 },
            ];
            instanceGroupsService.editInstanceGroups(mockUrl, selectedInstanceGroups)
                .then(() => {
                    expect(_postData).toEqual([
                        { id: 3, disassociate: true },
                        { id: 4, disassociate: true },
                        { id: 5, disassociate: true },
                        { id: 6, disassociate: true },
                        { id: 4, associate: true },
                        { id: 5, associate: true },
                        { id: 6, associate: true },
                        { id: 7, associate: true },
                        { id: 3, associate: true },
                    ]);
                })
                .finally(() => done());
        });
    });
});
