/*
 * Enzyme helpers for injecting top-level contexts
 * derived from https://lingui.js.org/guides/testing.html
 */
import React from 'react';
import { shape, object, string, arrayOf } from 'prop-types';
import { mount, shallow } from 'enzyme';
import { MemoryRouter, Router } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { ConfigProvider } from '../src/contexts/Config';

const language = 'en-US';
const intlProvider = new I18nProvider(
  {
    language,
    catalogs: {
      [language]: {},
    },
  },
  {}
);
const {
  linguiPublisher: { i18n: originalI18n },
} = intlProvider.getChildContext();

const defaultContexts = {
  linguiPublisher: {
    i18n: {
      ...originalI18n,
      _: key => {
        if (key.values) {
          Object.entries(key.values).forEach(([k, v]) => {
            key.id = key.id.replace(new RegExp(`\\{${k}\\}`), v);
          });
        }
        return key.id;
      }, // provide _ macro, for just passing down the key
      toJSON: () => '/i18n/',
    },
  },
  config: {
    ansible_version: null,
    custom_virtualenvs: [],
    version: null,
    me: { is_superuser: true },
    toJSON: () => '/config/',
  },
  router: {
    history_: {
      push: () => {},
      replace: () => {},
      createHref: () => {},
      listen: () => {},
      location: {
        hash: '',
        pathname: '',
        search: '',
        state: '',
      },
      toJSON: () => '/history/',
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
};

function wrapContexts(node, context) {
  const { config, router } = context;
  class Wrap extends React.Component {
    render() {
      // eslint-disable-next-line react/no-this-in-sfc
      const { children, ...props } = this.props;
      const component = React.cloneElement(children, props);
      if (router.history) {
        return (
          <ConfigProvider value={config}>
            <Router history={router.history}>{component}</Router>
          </ConfigProvider>
        );
      }
      return (
        <ConfigProvider value={config}>
          <MemoryRouter>{component}</MemoryRouter>
        </ConfigProvider>
      );
    }
  }

  return <Wrap>{node}</Wrap>;
}

function applyDefaultContexts(context) {
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

export function shallowWithContexts(node, options = {}) {
  const context = applyDefaultContexts(options.context);
  return shallow(wrapContexts(node, context));
}

export function mountWithContexts(node, options = {}) {
  const context = applyDefaultContexts(options.context);
  const childContextTypes = {
    linguiPublisher: shape({
      i18n: object.isRequired,
    }).isRequired,
    config: shape({
      ansible_version: string,
      custom_virtualenvs: arrayOf(string),
      version: string,
    }),
    router: shape({
      route: shape({
        location: shape({}),
        match: shape({}),
      }).isRequired,
      history: shape({}),
    }),
    ...options.childContextTypes,
  };
  return mount(wrapContexts(node, context), { context, childContextTypes });
}

/**
 * Wait for element(s) to achieve a desired state.
 *
 * @param[wrapper] - A ReactWrapper instance
 * @param[selector] - The selector of the element(s) to wait for.
 * @param[callback] - Callback to poll - by default this checks for a node count of 1.
 */
export function waitForElement(
  wrapper,
  selector,
  callback = el => el.length === 1
) {
  const interval = 100;
  return new Promise((resolve, reject) => {
    let attempts = 30;
    (function pollElement() {
      wrapper.update();
      const el = wrapper.find(selector);
      if (callback(el)) {
        return resolve(el);
      }
      if (--attempts <= 0) {
        const message = `Expected condition for <${selector}> not met: ${callback.toString()}`;
        return reject(new Error(message));
      }
      return setTimeout(pollElement, interval);
    })();
  });
}
