var webpack = require('webpack');
module.exports = {
    entry: {
        app: "./src/main.js",
        vendor: ["reconnectingwebsocket"],
    },
    output: {
        path: __dirname + "/js",
        filename:  "bundle.js",
    },
    plugins: [
         new webpack.optimize.CommonsChunkPlugin({ name: 'vendor', filename: 'vendor.bundle.js' })
    ]
};
