const path = require('path');

const _ = require('lodash');
const webpack = require('webpack');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const base = require('./webpack.base');

const CLIENT_PATH = path.resolve(__dirname, '../client');
const UI_PATH = path.resolve(__dirname, '..');
const INSTALL_RUNNING_ENTRY = path.join(CLIENT_PATH, 'installing.template.ejs');
const INSTALL_RUNNING_OUTPUT = path.join(UI_PATH, 'templates/ui/installing.html');
const CHUNKS = ['vendor', 'app'];

const production = {
    plugins: [
        new UglifyJSPlugin({
            compress: true,
            mangle: false
        }),
        new HtmlWebpackPlugin({
            alwaysWriteToDisk: true,
            template: INSTALL_RUNNING_ENTRY,
            filename: INSTALL_RUNNING_OUTPUT,
            inject: false,
            chunks: CHUNKS,
            chunksSortMode: chunk => chunk.names[0] === 'vendor' ? -1 : 1
        }),
        new webpack.DefinePlugin({
           'process.env': {
               'NODE_ENV': JSON.stringify('production')
            }
        })
    ]
};

production.plugins = base.plugins.concat(production.plugins);

module.exports = _.merge(base, production);
