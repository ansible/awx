const path = require('path');

const merge = require('webpack-merge');
const webpack = require('webpack');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const base = require('./webpack.base');

const CLIENT_PATH = path.resolve(__dirname, '../client');
const UI_PATH = path.resolve(__dirname, '..');
const CHUNKS = ['vendor', 'app'];

const production = {
    plugins: [
        new UglifyJSPlugin({
            compress: true,
            mangle: false
        }),
        new webpack.DefinePlugin({
            'process.env': {
                NODE_ENV: JSON.stringify('production')
            }
        })
    ]
};

module.exports = merge(base, production);
