import React, { Component } from 'react';
import { I18nProvider } from '@lingui/react';

import { HashRouter } from 'react-router-dom';

import { getLanguageWithoutRegionCode } from './util/language';
import ja from './locales/ja/messages';
import en from './locales/en/messages';

class RootProvider extends Component {
  render() {
    const { children } = this.props;

    const catalogs = { en, ja };
    const language = getLanguageWithoutRegionCode(navigator);

    return (
      <HashRouter>
        <I18nProvider language={language} catalogs={catalogs}>
          {children}
        </I18nProvider>
      </HashRouter>
    );
  }
}

export default RootProvider;
