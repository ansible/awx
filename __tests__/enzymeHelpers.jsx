/*
 * Enzyme helpers for injecting top-level contexts
 * derived from https://lingui.js.org/guides/testing.html
 */
import React from 'react';
import { shape, object, string, arrayOf, func } from 'prop-types';
import { mount, shallow } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import { ConfigProvider } from '../src/contexts/Config';
import { _NetworkProvider } from '../src/contexts/Network';
import { RootDialogProvider } from '../src/contexts/RootDialog';

const language = 'en-US';
const intlProvider = new I18nProvider(
  {
    language,
    catalogs: {
      [language]: {}
    }
  },
  {}
);
const {
  linguiPublisher: { i18n: originalI18n }
} = intlProvider.getChildContext();

const defaultContexts = {
  linguiPublisher: {
    i18n: {
      ...originalI18n,
      _: key => key.id, // provide _ macro, for just passing down the key
      toJSON: () => '/i18n/',
    },
  },
  config: {
    ansible_version: null,
    custom_virtualenvs: [],
    version: null,
    custom_logo: null,
    custom_login_info: null,
    toJSON: () => '/config/'
  },
  router: {
    history: {
      push: () => {},
      replace: () => {},
      createHref: () => {},
    },
    route: {
      location: {
        hash: '',
        pathname: '',
        search: '',
        state: '',
      },
      match: {
        params: {},
        isExact: false,
        path: '',
        url: '',
      },
    },
    toJSON: () => '/router/',
  },
  network: {
    api: {
      getConfig: () => {},
    },
    handleHttpError: () => {},
  },
  dialog: {}
};

const providers = {
  config: ConfigProvider,
  network: _NetworkProvider,
  dialog: RootDialogProvider,
};

function wrapContexts (node, context) {
  let wrapped = node;
  let isFirst = true;
  Object.keys(providers).forEach(key => {
    if (context[key]) {
      const Provider = providers[key];
      wrapped = (
        <Provider
          value={context[key]}
          i18n={isFirst ? defaultContexts.linguiPublisher.i18n : null}
        >
          {wrapped}
        </Provider>
      );
      isFirst = false;
    }
  });
  return wrapped;
}

function applyDefaultContexts (context) {
  if (!context) {
    return defaultContexts;
  }
  const newContext = {};
  Object.keys(defaultContexts).forEach(key => {
    newContext[key] = {
      ...defaultContexts[key],
      ...context[key],
    };
  });
  return newContext;
}

export function shallowWithContexts (node, options = {}) {
  const context = applyDefaultContexts(options.context);
  return shallow(wrapContexts(node, context));
}

export function mountWithContexts (node, options = {}) {
  const context = applyDefaultContexts(options.context);
  const childContextTypes = {
    linguiPublisher: shape({
      i18n: object.isRequired
    }).isRequired,
    config: shape({
      ansible_version: string,
      custom_virtualenvs: arrayOf(string),
      version: string,
      custom_logo: string,
      custom_login_info: string,
    }),
    router: shape({
      route: shape({
        location: shape({}),
        match: shape({}),
      }).isRequired,
      history: shape({}).isRequired,
    }),
    network: shape({
      api: shape({}).isRequired,
      handleHttpError: func.isRequired,
    }),
    dialog: shape({
      title: string,
      setRootDialogMessage: func,
      clearRootDialogMessage: func,
    }),
    ...options.childContextTypes
  };
  return mount(wrapContexts(node, context), { context, childContextTypes });
}
