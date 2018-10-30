module.exports = api => {
  api.cache(false);
  return {
    plugins: [
      '@babel/plugin-proposal-class-properties'
    ],
    presets: [
      ['@babel/preset-env', {
        targets: {
          node: '8.11'
        }
      }],
      '@babel/preset-react'
    ]
  };
};
