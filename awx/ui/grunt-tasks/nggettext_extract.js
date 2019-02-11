let source = [
    'client/features/**/*.js',
    'client/features/**/*.html',
    'client/lib/**/*.js',
    'client/lib/**/*.html',
    'client/src/**/*.js',
    'client/src/**/*.html',
    'client/*.ejs'
];

module.exports = {
    all: {
        options: {
            markerNames: ['_', 'N_'],
            moduleName: 't',
            moduleMethodString: 's',
            moduleMethodPlural: 'p'
        },
        files: {
            'po/ansible-tower-ui.pot': source
        }
    }
};
