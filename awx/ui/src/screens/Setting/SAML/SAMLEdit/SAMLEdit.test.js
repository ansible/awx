import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import SAMLEdit from './SAMLEdit';

jest.mock('../../../../api');

describe('<SAMLEdit />', () => {
  let wrapper;
  let history;

  beforeEach(() => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SAML_AUTO_CREATE_OBJECTS: true,
        SOCIAL_AUTH_SAML_CALLBACK_URL: 'https://towerhost/sso/complete/saml/',
        SOCIAL_AUTH_SAML_METADATA_URL: 'https://towerhost/sso/metadata/saml/',
        SOCIAL_AUTH_SAML_SP_ENTITY_ID: 'mock_id',
        SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: 'mock_cert',
        SOCIAL_AUTH_SAML_SP_PRIVATE_KEY: '$encrypted$',
        SOCIAL_AUTH_SAML_ORG_INFO: {},
        SOCIAL_AUTH_SAML_TECHNICAL_CONTACT: {
          givenName: 'Mock User',
          emailAddress: 'mockuser@example.com',
        },
        SOCIAL_AUTH_SAML_SUPPORT_CONTACT: {},
        SOCIAL_AUTH_SAML_ENABLED_IDPS: {},
        SOCIAL_AUTH_SAML_SP_EXTRA: {},
        SOCIAL_AUTH_SAML_EXTRA_DATA: [],
        SOCIAL_AUTH_SAML_ORGANIZATION_MAP: {},
        SOCIAL_AUTH_SAML_TEAM_MAP: {},
        SOCIAL_AUTH_SAML_ORGANIZATION_ATTR: {},
        SOCIAL_AUTH_SAML_TEAM_ATTR: {},
        SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR: {},
        SOCIAL_AUTH_SAML_SECURITY_CONFIG: {
          requestedAuthnContext: false,
        },
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/saml/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAMLEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('SAMLEdit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(
      wrapper.find('FormGroup[label="SAML Service Provider Entity ID"]').length
    ).toBe(1);
    expect(
      wrapper.find(
        'FormGroup[label="Automatically Create Organizations and Teams on SAML Login"]'
      ).length
    ).toBe(1);
    expect(
      wrapper.find(
        'FormGroup[label="SAML Service Provider Public Certificate"]'
      ).length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Service Provider Private Key"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Service Provider Organization Info"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Service Provider Technical Contact"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Service Provider Support Contact"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Enabled Identity Providers"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Organization Map"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="SAML Team Map"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Organization Attribute Mapping"]')
        .length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="SAML Team Attribute Mapping"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="SAML Security Config"]').length).toBe(
      1
    );
    expect(
      wrapper.find(
        'FormGroup[label="SAML Service Provider extra configuration data"]'
      ).length
    ).toBe(1);
    expect(
      wrapper.find(
        'FormGroup[label="SAML IDP to extra_data attribute mapping"]'
      ).length
    ).toBe(1);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(0);
    expect(wrapper.find('RevertAllAlert')).toHaveLength(0);
    await act(async () => {
      wrapper
        .find('button[aria-label="Revert all to default"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('RevertAllAlert')).toHaveLength(1);
    await act(async () => {
      wrapper
        .find('RevertAllAlert button[aria-label="Confirm revert all"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('saml');
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper.find('input#SOCIAL_AUTH_SAML_SP_ENTITY_ID').simulate('change', {
        target: { value: 'new_id', name: 'SOCIAL_AUTH_SAML_SP_ENTITY_ID' },
      });
      wrapper
        .find(
          'FormGroup[fieldId="SOCIAL_AUTH_SAML_TECHNICAL_CONTACT"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      SAML_AUTO_CREATE_OBJECTS: true,
      SOCIAL_AUTH_SAML_ENABLED_IDPS: {},
      SOCIAL_AUTH_SAML_EXTRA_DATA: [],
      SOCIAL_AUTH_SAML_ORGANIZATION_ATTR: {},
      SOCIAL_AUTH_SAML_ORGANIZATION_MAP: {},
      SOCIAL_AUTH_SAML_ORG_INFO: {},
      SOCIAL_AUTH_SAML_SP_ENTITY_ID: 'new_id',
      SOCIAL_AUTH_SAML_SP_EXTRA: {},
      SOCIAL_AUTH_SAML_SP_PRIVATE_KEY: '$encrypted$',
      SOCIAL_AUTH_SAML_SP_PUBLIC_CERT: 'mock_cert',
      SOCIAL_AUTH_SAML_SUPPORT_CONTACT: {},
      SOCIAL_AUTH_SAML_TEAM_ATTR: {},
      SOCIAL_AUTH_SAML_USER_FLAGS_BY_ATTR: {},
      SOCIAL_AUTH_SAML_TEAM_MAP: {},
      SOCIAL_AUTH_SAML_TECHNICAL_CONTACT: {},
      SOCIAL_AUTH_SAML_SECURITY_CONFIG: {
        requestedAuthnContext: false,
      },
    });
  });

  test('should navigate to saml detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual('/settings/saml/details');
  });

  test('should navigate to saml detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/settings/saml/details');
  });

  test('should display error message on unsuccessful submission', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    SettingsAPI.updateAll.mockImplementation(() => Promise.reject(error));
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should display ContentError on throw', async () => {
    SettingsAPI.readCategory.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <SAMLEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
