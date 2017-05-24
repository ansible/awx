export default
    ['Rest', function(Rest) {
        return {
            addInstanceGroups: function(url, instance_groups) {
                let groups = (instance_groups || []);
                Rest.setUrl(url);
                let defers = groups.map((group) => Rest.post(group));
                return Promise.all(defers);
            },
            editInstanceGroups: function(url, instance_groups) {
                Rest.setUrl(url);
                let currentGroups = Rest.get()
                    .then(({data}) => {
                        return data.results.map((i) => i.id);
                    });

                return currentGroups.then(function(current) {

                    let groupsToAdd = (instance_groups || [])
                        .map(val => val.id);

                    let groupsToDisassociate = current
                        .filter(val => groupsToAdd
                            .indexOf(val) === -1)
                        .map(val => ({id: val, disassociate: true}));

                    let groupsToAssociate = groupsToAdd
                        .filter(val => current
                            .indexOf(val) === -1)
                        .map(val => ({id: val, associate: true}));

                    let pass = groupsToDisassociate
                        .concat(groupsToAssociate);

                    Rest.setUrl(url);
                    let defers = pass.map((group) => Rest.post(group));
                    Promise.resolve(defers);
                });
            }
        };
}];