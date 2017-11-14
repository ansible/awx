var webpack = require('webpack');
module.exports = {
    entry: {
        app: "./src-instrumented/main.js",
        vendor: ["angular",
                 "angular-ui-router",
                 "hamsterjs",
                 "angular-mousewheel",
                 "reconnectingwebsocket",
                 "angular-xeditable"]
    },
    output: {
        path: __dirname + "/js",
        filename:  "bundle-instrumented.js",
    },
    plugins: [
         new webpack.ProvidePlugin({Hamster: 'hamsterjs'}),
         new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.bundle.js' })
    ]
};
