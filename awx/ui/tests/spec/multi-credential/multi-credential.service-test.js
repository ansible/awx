'use strict';

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

    describe('saveExtraCredentials', () => {
        xit('should handle creds as array of objects and array of ids', () => {
            expect(false).toBe(true);
        });

        xit('should post creds with add payload', () => {
            expect(false).toBe(true);
        });

        xit('should post creds with disassociate payload', () => {
            expect(false).toBe(true);
        });

        xit('should call ProcessErrors when post fails', () => {
            expect(false).toBe(true);
        });
    });

    describe('findChangedExtraCredentials', () => {
        xit('should find which creds to add and post them', () => {
            expect(false).toBe(true);
        });

        xit('should find which creds to remove and disassociate them', () => {
            expect(false).toBe(true);
        });

        xit('should not post/disassociate non-changed creds', () => {
            expect(false).toBe(true);
        });

        xit('should call ProcessErrors when any get/post fails', () => {
            expect(false).toBe(true);
        });
    });

    describe('getCredentialTypes', () => {
        xit('should get cred types and return them directly, as well ' +
            'as options for building credential type select box', () => {
                expect(false).toBe(true);
            });

        xit('should call ProcessErrors when getting cred types fails', () => {
            expect(false).toBe(true);
        });
    });

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

        it('should return array of selected credentials (populated, not read only)', () => {
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
                    readOnly: false,
                    kind: 'SSH:'
                },
                {
                    name: 'aws',
                    id: 4,
                    postType: 'extra',
                    readOnly: false,
                    kind: 'Amazon Web Services:'
                },
                {
                    name: 'gce',
                    id: 5,
                    postType: 'extra',
                    readOnly: false,
                    kind: 'Google Compute Engine:'
                }
            ];

            let actual = MultiCredentialService
                .updateCredentialTags(creds, typeOpts);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });

        it('should return array of selected credentials (populated, read only)', () => {
            let creds = {
                machine: {
                    credential_type: 1,
                    id: 3,
                    name: 'ssh',
                    readOnly: true
                },
                extra: [
                    {
                        credential_type: 2,
                        id: 4,
                        name: 'aws',
                        readOnly: true
                    },
                    {
                        credential_type: 3,
                        id: 5,
                        name: 'gce',
                        readOnly: true
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
                    readOnly: true,
                    kind: 'SSH:'
                },
                {
                    name: 'aws',
                    id: 4,
                    postType: 'extra',
                    readOnly: true,
                    kind: 'Amazon Web Services:'
                },
                {
                    name: 'gce',
                    id: 5,
                    postType: 'extra',
                    readOnly: true,
                    kind: 'Google Compute Engine:'
                }
            ];

            let actual = MultiCredentialService
                .updateCredentialTags(creds, typeOpts);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });
    });

    describe('removeCredential', () => {
        it('should remove machine cred from structured obj and tag arr', () => {
            let credToRemove = 3;

            let structuredObj = {
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

            let tagArr = [
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

            let expected = [
                {
                    machine: null,
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
                },
                [
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
                ]
            ];

            let actual = MultiCredentialService
                .removeCredential(credToRemove, structuredObj, tagArr);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });

        it('should remove extra cred from structured obj and tag arr', () => {
            let credToRemove = 4;

            let structuredObj = {
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

            let tagArr = [
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

            let expected = [
                {
                    machine: {
                        credential_type: 1,
                        id: 3,
                        name: 'ssh'
                    },
                    extra: [
                        {
                            credential_type: 3,
                            id: 5,
                            name: 'gce'
                        }
                    ]
                },
                [
                    {
                        name: 'ssh',
                        id: 3,
                        postType: 'machine',
                        kind: 'SSH:'
                    },
                    {
                        name: 'gce',
                        id: 5,
                        postType: 'extra',
                        kind: 'Google Compute Engine:'
                    }
                ]
            ];

            let actual = MultiCredentialService
                .removeCredential(credToRemove, structuredObj, tagArr);

            let equal = _.isEqual(expected.sort(), actual.sort());

            expect(equal).toBe(true);
        });
    });

    describe('loadCredentials', () => {
        xit('should call to get machine credential data', () => {
            expect(false).toBe(true);
        });

        xit('should call ProcessErrors if machine cred get fails', () => {
            expect(false).toBe(true);
        });

        xit('should call to get extra credentials data', () => {
            expect(false).toBe(true);
        });

        xit('should call ProcessErrors if extra creds get fails', () => {
            expect(false).toBe(true);
        });

        xit('should call to get credential types', () => {
            expect(false).toBe(true);
        });

        xit('should call to update cred tags once GETs have completed', () => {
            expect(false).toBe(true);
        });
    });
});
