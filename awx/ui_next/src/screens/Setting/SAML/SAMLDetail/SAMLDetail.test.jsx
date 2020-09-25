import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import SAMLDetail from './SAMLDetail';

jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    SOCIAL_AUTH_SAML_CALLBACK_URL: 'https://towerhost/sso/complete/saml/',
    SOCIAL_AUTH_SAML_METADATA_URL: 'https://towerhost/sso/metadata/saml/',
    SOCIAL_AUTH_SAML_SP_ENTITY_ID: 'mock_id',
    SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: 'mock_cert',
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
  },
});

describe('<SAMLDetail />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAMLDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('SAMLDetail').length).toBe(1);
  });

  test('should render expected details', () => {
    assertDetail(
      wrapper,
      'SAML Assertion Consumer Service (ACS) URL',
      'https://towerhost/sso/complete/saml/'
    );
    assertDetail(
      wrapper,
      'SAML Service Provider Metadata URL',
      'https://towerhost/sso/metadata/saml/'
    );
    assertDetail(wrapper, 'SAML Service Provider Entity ID', 'mock_id');
    assertDetail(
      wrapper,
      'SAML Service Provider Public Certificate',
      'mock_cert'
    );
    assertDetail(
      wrapper,
      'SAML Service Provider Private Key',
      'Not configured'
    );
    assertVariableDetail(
      wrapper,
      'SAML Service Provider Organization Info',
      '{}'
    );
    assertVariableDetail(
      wrapper,
      'SAML Service Provider Technical Contact',
      '{}'
    );
    assertVariableDetail(
      wrapper,
      'SAML Service Provider Support Contact',
      '{}'
    );
    assertVariableDetail(wrapper, 'SAML Enabled Identity Providers', '{}');
    assertVariableDetail(wrapper, 'SAML Security Config', '{}');
    assertVariableDetail(
      wrapper,
      'SAML Service Provider extra configuration data',
      '{}'
    );
    assertVariableDetail(
      wrapper,
      'SAML IDP to extra_data attribute mapping',
      '[]'
    );
    assertVariableDetail(wrapper, 'SAML Organization Map', '{}');
    assertVariableDetail(wrapper, 'SAML Team Map', '{}');
    assertVariableDetail(wrapper, 'SAML Organization Attribute Mapping', '{}');
    assertVariableDetail(wrapper, 'SAML Team Attribute Mapping', '{}');
  });

  test('should hide edit button from non-superusers', async () => {
    const config = {
      me: {
        is_superuser: false,
      },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAMLDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAMLDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
