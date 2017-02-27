module.exports = {
    all: {
        options: {
            markerNames: ['_', 'N_']
        },
        files: {
            'po/ansible-tower-ui.pot': ['client/src/**/*.js',
                                        'client/src/**/*.html']
        }
    },
};
