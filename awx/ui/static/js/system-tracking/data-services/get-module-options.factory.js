var moduleConfig =
    {   'packages':
            {   compareKey: ['release', 'version'],
                nameKey: 'name',
                displayType: 'flat'
            },
        'services':
            {   compareKey: ['state', 'source'],
                nameKey: 'name',
                displayType: 'flat'
            },
        'files':
            {   compareKey: ['size', 'mode', 'md5', 'mtime', 'gid', 'uid'],
                nameKey: 'path',
                displayType: 'flat'
            },
        'custom':
            {   displayType: 'nested'
            }
    };

function makeModule(option) {
    var name = option[0];
    var displayName = option[1];
    var config = moduleConfig.hasOwnProperty(name) ?
                    moduleConfig[name] : moduleConfig.custom;

    return {
        name: name,
        displayName: displayName,
        compareKey: config.compareKey,
        nameKey: config.nameKey,
        displayType: config.displayType
    };
}

function factory(hostId, rest, getBasePath, _) {
    var url = [ getBasePath('hosts') + hostId,
                'fact_versions'
              ].join('/');

    rest.setUrl(url);
    return _(rest.options())
        .then(function(response) {
            return response.data.actions.GET.module.choices;
        }).thenMap(makeModule);
}

export default
    [   'Rest',
        'GetBasePath',
        'lodashAsPromised',
        function(rest, getBasePath, lodash) {
            return _.partialRight(factory, rest, getBasePath, lodash);
        }
    ];
