module.exports = {
    all: {
        options: {
            format: 'json'
        },
        files: [{
            expand: true,
            dot: true,
            dest: 'client/languages',
            cwd: 'po',
            ext: '.json',
            src: ['*.po']
        }]
    }
};

