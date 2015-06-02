var moduleConfig =
    {   'packages':
            {   compareKey: ['release', 'version'],
                nameKey: 'name',
                displayType: 'flat',
                sortKey: 1,
                factTemplate: "{{epoch|append:':'}}{{version}}-{{release}}{{arch|prepend:'.'}}"
            },
        'services':
            {   compareKey: ['state', 'source'],
                nameKey: 'name',
                displayType: 'flat',
                factTemplate: '{{state}} ({{source}})',
                sortKey: 2
            },
        'files':
            {   compareKey: ['size', 'mode', 'md5', 'mtime', 'gid', 'uid'],
                nameKey: 'path',
                displayType: 'flat',
                sortKey: 3
            },
        'ansible':
            {   displayType: 'nested',
                sortKey: 4
            },
        'custom':
            {   displayType: 'nested'
            }
    };

function makeModule(option, index) {
    var name = option[0];
    var displayName = option[1];
    var config = moduleConfig.hasOwnProperty(name) ?
                    moduleConfig[name] : moduleConfig.custom;
    var modulesCount = _.keys(moduleConfig).length - 1;

    config.name = name;
    config.displayName = displayName;

    // Use index to sort custom modules,
    // offset by built-in modules since
    // they have a hardcoded sort key
    //
    if (_.isUndefined(config.sortKey)) {
        config.sortKey = (index - 1) + modulesCount;
    }

    return config;
}

function factory(hostId, rest, getBasePath, _) {
    var url = [ getBasePath('hosts') + hostId,
                'fact_versions'
              ].join('/');

    rest.setUrl(url);
    return _(rest.options())
        .then(function(response) {
            var choices = response.data.actions.GET.module.choices;
            return _.sortBy(choices, '1');
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
