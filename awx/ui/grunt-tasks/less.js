module.exports = {
    options: {
      options : {
        plugins : [ new (require('less-plugin-autoprefix'))({browsers : [ "last 2 versions" ]}) ]
      }
    },
    dev: {
        files: [{
            dest: 'static/tower.min.css',
            src: [
                'client/legacy-styles/*.less',
                'client/src/**/*.less',
            ]
        }],
        options: {
            sourceMap: true
        }
    },

    prod: {
        files: {
            'static/tower.min.css': [
                'client/legacy-styles/*.less',
                'client/src/**/*.less',
            ]
        },
        options: {
            compress: true,
        }
    }
};
