'use strict'

describe('MultiCredentialService', () => {
    let MultiCredentialService;

    beforeEach(angular.mock.module('multiCredential',
        ($provide) => {
            ['Rest', 'ProcessErrors', '$q', 'GetBasePath']
                .forEach(item => $provide.value(item, {}));
        }));

    beforeEach(angular.mock.inject((_MultiCredentialService_) => {
        MultiCredentialService = _MultiCredentialService_;
    }));

    describe('updateCredentialTags', () => {
        it('should return array of selected credentials (empty)', () => {
            let creds = {
                machine: null,
                extra: []
            };

            let typeOpts = [];

            let expected = [];

            let actual = MultiCredentialService
                .updateCredentialTags(creds, typeOpts);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });

        it('should return array of selected credentials (populated)', () => {
            let creds = {
                machine: {
                    credential_type: 1,
                    id: 3,
                    name: 'ssh'
                },
                extra: [
                    {
                        credential_type: 2,
                        id: 4,
                        name: 'aws'
                    },
                    {
                        credential_type: 3,
                        id: 5,
                        name: 'gce'
                    }
                ]
            };

            let typeOpts = [
                {
                    name: 'SSH',
                    value: 1
                },
                {
                    name: 'Amazon Web Services',
                    value: 2
                },
                {
                    name: 'Google Compute Engine',
                    value: 3
                }
            ];

            let expected = [
                {
                    name: 'ssh',
                    id: 3,
                    postType: 'machine',
                    kind: 'SSH:'
                },
                {
                    name: 'aws',
                    id: 4,
                    postType: 'extra',
                    kind: 'Amazon Web Services:'
                },
                {
                    name: 'gce',
                    id: 5,
                    postType: 'extra',
                    kind: 'Google Compute Engine:'
                }
            ];

            let actual = MultiCredentialService
                .updateCredentialTags(creds, typeOpts);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });
    });
});
