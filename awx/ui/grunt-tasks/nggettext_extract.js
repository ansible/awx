let source = [
    'client/features/**/*.js',
    'client/features/**/*.html',
    'client/lib/**/*.js',
    'client/lib/**/*.html',
    'client/src/**/*.js',
    'client/src/**/*.html'
];

module.exports = {
    all: {
        options: {
            markerNames: ['_', 'N_', 't']
        },
        files: {
            'po/ansible-tower-ui.pot': source
        }
    }
};
