module.exports = {
    all: {
        options: {
            markerNames: ['_', 'N_']
        },
        files: {
            'po/ansible-tower.pot': ['client/src/**/*.js',
                                     'client/src/**/*.html']
        }
    },
};
