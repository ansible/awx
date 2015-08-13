var typesSupportingIsolatedScope =
    [   'multiselect',
        'multiplechoice'
    ];

function typeSupportsIsolatedScope(type) {
    return _.include(typesSupportingIsolatedScope, type);
}

function getIsolatedScope(question, oldScope) {
    var newScope = oldScope.$new();
    newScope.question = question;
    return newScope;
}

export default
    function() {
        return function(question, oldScope) {
            if (typeSupportsIsolatedScope(question.type)) {
                return getIsolatedScope(question, oldScope);
            } else {
                return oldScope;
            }
        };
    }
