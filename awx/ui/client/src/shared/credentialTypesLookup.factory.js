export default ['Rest', 'GetBasePath', 'ProcessErrors',
function(Rest, GetBasePath, ProcessErrors) {
    return function() {
        Rest.setUrl(GetBasePath('credential_types'));
        return Rest.get()
            .then(({data}) => {
                var val = {};
                data.results.forEach(type => {
                    val[type.name] = type.id;
                });
                return val;
            })
            .catch(({data, status}) => {
                ProcessErrors(null, data, status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to GET credential types.  Returned status' +
                        status
                });
            });
    };
}];
