//webpack.config.js
const path = require('path');
const {merge} = require('webpack-merge');

const defaultConfig = {
  resolve: {
    extensions: ['.ts', '.tsx', '.js'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        loader: 'ts-loader',
      },
    ],
  },
};

const baseConfig = {
  entry: {
    main: './src/base.ts',
  },
  output: {
    path: path.resolve(__dirname, './app/static'),
    filename: 'js/base.js', // <--- Will be compiled to this single file
  },
};

const userConfig = {
  entry: {
    main: './src/user.ts',
  },
  output: {
    path: path.resolve(__dirname, './app/static'),
    filename: 'js/user.js', // <--- Will be compiled to this single file
  },
};

const adminConfig = {
  entry: {
    main: './src/admin.ts',
  },
  output: {
    path: path.resolve(__dirname, './app/static'),
    filename: 'js/admin.js', // <--- Will be compiled to this single file
  },
};
const serviceConfig = {
  entry: {
    main: './src/service.ts',
  },
  output: {
    path: path.resolve(__dirname, './app/static'),
    filename: 'js/service.js', // <--- Will be compiled to this single file
  },
};
const regionConfig = {
  entry: {
    main: './src/region.ts',
  },
  output: {
    path: path.resolve(__dirname, './app/static'),
    filename: 'js/region.js', // <--- Will be compiled to this single file
  },
};
const configs = [
  baseConfig,
  userConfig,
  adminConfig,
  serviceConfig,
  regionConfig,
].map(conf => merge(defaultConfig, conf));

module.exports = configs;
