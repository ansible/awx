import React from 'react';

// eslint-disable-next-line import/prefer-default-export
export const ConfigContext = React.createContext({});

export const ConfigProvider = ConfigContext.Provider;
export const Config = ConfigContext.Consumer;
