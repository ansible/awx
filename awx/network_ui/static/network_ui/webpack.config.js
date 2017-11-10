var webpack = require('webpack');
module.exports = {
    entry: {
        app: "./src/main.js",
        vendor: ["angular",
                 "angular-ui-router",
                 "jquery",
                 "jquery-ui",
                 "hamsterjs",
                 "angular-mousewheel",
                 "reconnectingwebsocket",
                 "angular-xeditable"]
    },
    output: {
        path: __dirname + "/js",
        filename:  "bundle.js",
    },
    plugins: [
         new webpack.ProvidePlugin({Hamster: 'hamsterjs'}),
         new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.bundle.js' })
    ]
};
