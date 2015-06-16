var moduleConfig =
    {   'packages':
            {   compareKey: ['release', 'version'],
                nameKey: 'name',
                sortKey: 1,
                factTemplate: "{{epoch|append:':'}}{{version}}-{{release}}{{arch|prepend:'.'}}"
            },
        'services':
            {   compareKey: ['state', 'source'],
                nameKey: 'name',
                factTemplate: '{{state}} ({{source}})',
                sortKey: 2
            },
        'files':
            {   compareKey: ['size', 'mode', 'md5', 'mtime', 'gid', 'uid'],
                keyNameMap:
                    {   'uid': 'ownership'
                    },
                factTemplate:
                    {   'uid': 'user id: {{uid}}, group id: {{gid}}',
                        'mode': true,
                        'md5': true,
                        'mtime': '{{mtime|formatEpoch}}'
                    },
                nameKey: 'path',
                sortKey: 3
            },
        'ansible':
            {   sortKey: 4
            },
        'custom':
            {
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
