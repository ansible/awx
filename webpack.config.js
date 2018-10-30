const path = require('path');
const webpack = require('webpack');

const TARGET_PORT = 8043;
const TARGET = `https://localhost:${TARGET_PORT}`;

module.exports = {
  entry: './src/index.jsx',
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      },
      {
        test: /\.s?[ac]ss$/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
          { loader: 'sass-loader' },
        ]
      },
      {
        test: /\.(woff(2)?|ttf|eot)(\?v=\d+\.\d+\.\d+)?$/,
        use: [{
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'assets/fonts/',
            publicPatH: '../',
            includePaths: [
              'node_modules/@patternfly/patternfly-next/assets/fonts',
            ]
          }
        }]
      },
      {
        test: /\.(jpg|png|gif|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: [{
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'assets/images/',
            publicPatH: '../',
            includePaths: [
              'node_modules/@patternfly/patternfly-next/assets/images',
            ]
          }
        }]
      }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx', '.css']
  },
  output: {
    path: path.resolve(__dirname, '/dist'),
    publicPath: '/',
    filename: 'bundle.js'
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin()
  ],
  devServer: {
    contentBase: './dist',
    hot: true,
    inline: true,
    stats: 'minimal',
    host: '127.0.0.1',
    https: true,
    port: 3001,
    clientLogLevel: 'none',
    proxy: [
      {
        context: '/api/login/',
        target: TARGET,
        secure: false,
        ws: false,
        headers: {
          Host: `localhost:${TARGET_PORT}`,
          Origin: TARGET,
          Referer: `${TARGET}/`
        }
      },
      {
        context: '/api',
        target: TARGET,
        secure: false,
        ws: false,
        bypass: req => (req.originalUrl.includes('hot-update.json') || req.originalUrl.includes('login')),
      },
      {
        context: '/websocket',
        target: TARGET,
        secure: false,
        ws: true
      }
    ]
  }
};
