var AutoPrefixer = require('less-plugin-autoprefix');

var autoPrefixer = new AutoPrefixer({
    browsers: [ 'last 2 versions' ]
});

module.exports = {
    dev: {
        files: {
            'static/css/app.css': 'client/lib/theme/index.less'
        },
        options: {
            sourceMap: true,
            plugins: [ autoPrefixer ]
        }
    },
    prod: {
        files: {
            'static/css/app.css': 'client/lib/theme/index.less'
        },
        options: {
            compress: true,
            sourceMap: false,
            plugins: [ autoPrefixer ]
        }
    }
};
