/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['GetBasePath', '$q', 'Rest', 'i18n',
    function(GetBasePath, $q, Rest, i18n) {
        var url = GetBasePath('settings') + 'all';

        return {
            getConfigurationOptions: function() {
                var deferred = $q.defer();
                var returnData = {};

                Rest.setUrl(url);
                Rest.options()
                    .then(({data}) => {
                        // Compare GET actions with PUT actions and flag discrepancies
                        // for disabling in the UI
                        //
                        // since OAUTH2_PROVIDER returns two of the keys in a nested format,
                        // we need to split those out into the root of the options payload
                        // in order for them to be consumed
                        var appendOauth2ProviderKeys = (optsFromAPI) => {
                            var unnestOauth2ProviderKey = (key, help_text, label, parentKey) => {
                                optsFromAPI[key] = _.cloneDeep(optsFromAPI[parentKey]);
                                optsFromAPI[key].label = label;
                                optsFromAPI[key].help_text = help_text;
                                optsFromAPI[key].type = optsFromAPI[parentKey].child.type;
                                optsFromAPI[key].min_value = optsFromAPI[parentKey].child.min_value;
                                if (optsFromAPI[parentKey].default) {
                                    optsFromAPI[key].default = optsFromAPI[parentKey].default[key];
                                }
                                delete optsFromAPI[key].child;
                            };
                            if (optsFromAPI.OAUTH2_PROVIDER) {
                                unnestOauth2ProviderKey('ACCESS_TOKEN_EXPIRE_SECONDS',
                                    i18n._('The duration (in seconds) access tokens remain valid since their creation.'),
                                    i18n._('Access Token Expiration'),
                                    'OAUTH2_PROVIDER');
                                unnestOauth2ProviderKey('REFRESH_TOKEN_EXPIRE_SECONDS',
                                    i18n._('The duration (in seconds) refresh tokens remain valid after the expiration of their associated access token.'),
                                    i18n._('Refresh Token Expiration'),
                                    'OAUTH2_PROVIDER');
                                unnestOauth2ProviderKey('AUTHORIZATION_CODE_EXPIRE_SECONDS',
                                    i18n._('The duration (in seconds) authorization codes remain valid since their creation.'),
                                    i18n._('Authorization Code Expiration'),
                                    'OAUTH2_PROVIDER');
                            }
                            return optsFromAPI;
                        };
                        var getActions = appendOauth2ProviderKeys(data.actions.GET);
                        var getKeys = _.keys(getActions);
                        var putActions = data.actions.PUT ? appendOauth2ProviderKeys(data.actions.PUT) : {};

                        _.each(getKeys, function(key) {
                            if(putActions && putActions[key]) {
                                returnData[key] = putActions[key];
                            } else {
                                returnData[key] = _.extend(getActions[key], {
                                                        required: false,
                                                        disabled: true
                                                    });
                            }
                        });

                        deferred.resolve(returnData);
                    })
                    .catch(({error}) => {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            patchConfiguration: function(body) {
                var deferred = $q.defer();

                Rest.setUrl(url);
                Rest.patch(body)
                    .then(({data}) => {
                        deferred.resolve(data);
                    })
                    .catch((error) => {
                        deferred.reject(error);
                    });

                return deferred.promise;
            },

            getCurrentValues: function() {
                var deferred = $q.defer();
                Rest.setUrl(url);
                Rest.get()
                    .then(({data}) => {
                        deferred.resolve(data);
                    })
                    .catch((error) => {
                        deferred.reject(error);
                    });

                return deferred.promise;
            }
        };
    }
];
