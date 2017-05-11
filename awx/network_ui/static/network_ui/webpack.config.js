var webpack = require('webpack');
module.exports = {
    entry: {
        app: "./src/main.js",
        vendor: ["hamsterjs",
                 "angular-mousewheel",
                 "ngTouch",
                 "reconnectingwebsocket"],
    },
    output: {
        path: __dirname + "/js",
        filename:  "bundle.js",
    },
    plugins: [
         new webpack.ProvidePlugin({Hamster: 'hamsterjs'}),
         new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.bundle.js' })
    ],
    resolve: {
        alias: {
            ngTouch: __dirname + "/vendor/ngTouch.js"
        }
    }
};
