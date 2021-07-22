import React, { useContext } from 'react';

export const SettingsContext = React.createContext({});
export const SettingsProvider = SettingsContext.Provider;

export const useSettings = () => useContext(SettingsContext);
