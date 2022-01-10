import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import { SettingsProvider } from 'contexts/Settings';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import SAML from './SAML';

jest.mock('../../../api');

describe('<SAML />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_SAML_CALLBACK_URL: 'https://towerhost/sso/complete/saml/',
        SOCIAL_AUTH_SAML_METADATA_URL: 'https://towerhost/sso/metadata/saml/',
        SOCIAL_AUTH_SAML_SP_ENTITY_ID: '',
        SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: '',
        SOCIAL_AUTH_SAML_SP_PRIVATE_KEY: '',
        SOCIAL_AUTH_SAML_ORG_INFO: {},
        SOCIAL_AUTH_SAML_TECHNICAL_CONTACT: {},
        SOCIAL_AUTH_SAML_SUPPORT_CONTACT: {},
        SOCIAL_AUTH_SAML_ENABLED_IDPS: {},
        SOCIAL_AUTH_SAML_SECURITY_CONFIG: {},
        SOCIAL_AUTH_SAML_SP_EXTRA: {},
        SOCIAL_AUTH_SAML_EXTRA_DATA: [],
        SOCIAL_AUTH_SAML_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_SAML_TEAM_MAP: {},
        SOCIAL_AUTH_SAML_ORGANIZATION_ATTR: {},
        SOCIAL_AUTH_SAML_TEAM_ATTR: {},
        SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR: {},
        SAML_AUTO_CREATE_OBJECTS: false,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render SAML details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/saml/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAML />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('SAMLDetail').length).toBe(1);
  });

  test('should render SAML edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/saml/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAML />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('SAMLEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/saml/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<SAML />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
