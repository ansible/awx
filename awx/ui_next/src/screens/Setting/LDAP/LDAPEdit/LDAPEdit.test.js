import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { useRouteMatch } from 'react-router-dom';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockLDAP from '../../shared/data.ldapSettings.json';
import LDAPEdit from './LDAPEdit';

jest.mock('../../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: jest.fn(),
}));

describe('<LDAPEdit />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    SettingsAPI.readCategory.mockResolvedValue({ data: mockLDAP });
    history = createMemoryHistory({
      initialEntries: ['/settings/ldap/default/edit'],
    });
    useRouteMatch.mockImplementation(() => ({
      url: '/settings/ldap/default/edit',
      path: '/settings/ldap/:category/edit',
      params: { category: 'default' },
    }));
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LDAPEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('LDAPEdit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(wrapper.find('FormGroup[label="LDAP Server URI"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Bind DN"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Bind Password"]').length).toBe(
      1
    );
    expect(wrapper.find('FormGroup[label="LDAP User Search"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="LDAP User DN Template"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="LDAP User Attribute Map"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Group Search"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Group Type"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="LDAP Group Type Parameters"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Require Group"]').length).toBe(
      1
    );
    expect(wrapper.find('FormGroup[label="LDAP Deny Group"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Start TLS"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="LDAP User Flags By Group"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="LDAP Organization Map"]').length
    ).toBe(1);
    expect(wrapper.find('FormGroup[label="LDAP Team Map"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[fieldId="AUTH_LDAP_SERVER_URI"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[fieldId="AUTH_LDAP_5_SERVER_URI"]').length
    ).toBe(0);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
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
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      AUTH_LDAP_BIND_DN: '',
      AUTH_LDAP_BIND_PASSWORD: '',
      AUTH_LDAP_CONNECTION_OPTIONS: {
        OPT_NETWORK_TIMEOUT: 30,
        OPT_REFERRALS: 0,
      },
      AUTH_LDAP_DENY_GROUP: null,
      AUTH_LDAP_GROUP_SEARCH: [],
      AUTH_LDAP_GROUP_TYPE: 'MemberDNGroupType',
      AUTH_LDAP_GROUP_TYPE_PARAMS: {
        member_attr: 'member',
        name_attr: 'cn',
      },
      AUTH_LDAP_ORGANIZATION_MAP: {},
      AUTH_LDAP_REQUIRE_GROUP: null,
      AUTH_LDAP_SERVER_URI: '',
      AUTH_LDAP_START_TLS: false,
      AUTH_LDAP_TEAM_MAP: {},
      AUTH_LDAP_USER_ATTR_MAP: {},
      AUTH_LDAP_USER_DN_TEMPLATE: null,
      AUTH_LDAP_USER_FLAGS_BY_GROUP: {},
      AUTH_LDAP_USER_SEARCH: [],
    });
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper
        .find(
          'FormGroup[fieldId="AUTH_LDAP_BIND_PASSWORD"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper
        .find(
          'FormGroup[fieldId="AUTH_LDAP_BIND_DN"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper.find('input#AUTH_LDAP_SERVER_URI').simulate('change', {
        target: {
          value: 'ldap://mock.example.com',
          name: 'AUTH_LDAP_SERVER_URI',
        },
      });
      wrapper.find('CodeEditor#AUTH_LDAP_TEAM_MAP').invoke('onChange')(
        '{\n"LDAP Sales":{\n"organization":\n"mock org"\n}\n}'
      );
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      AUTH_LDAP_BIND_DN: '',
      AUTH_LDAP_BIND_PASSWORD: '',
      AUTH_LDAP_DENY_GROUP: '',
      AUTH_LDAP_GROUP_SEARCH: [],
      AUTH_LDAP_GROUP_TYPE: 'MemberDNGroupType',
      AUTH_LDAP_GROUP_TYPE_PARAMS: { name_attr: 'cn', member_attr: 'member' },
      AUTH_LDAP_ORGANIZATION_MAP: {},
      AUTH_LDAP_REQUIRE_GROUP: 'CN=Service Users,OU=Users,DC=example,DC=com',
      AUTH_LDAP_SERVER_URI: 'ldap://mock.example.com',
      AUTH_LDAP_START_TLS: false,
      AUTH_LDAP_USER_ATTR_MAP: {},
      AUTH_LDAP_USER_DN_TEMPLATE: 'uid=%(user)s,OU=Users,DC=example,DC=com',
      AUTH_LDAP_USER_FLAGS_BY_GROUP: {},
      AUTH_LDAP_USER_SEARCH: [],
      AUTH_LDAP_TEAM_MAP: {
        'LDAP Sales': {
          organization: 'mock org',
        },
      },
    });
  });

  test('should navigate to ldap default detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual('/settings/ldap/default/details');
  });

  test('should navigate to ldap default detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/settings/ldap/default/details');
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
          <LDAPEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should display ldap category 5 edit form', async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/ldap/5/edit'],
    });
    useRouteMatch.mockImplementation(() => ({
      url: '/settings/ldap/5/edit',
      path: '/settings/ldap/:category/edit',
      params: { category: '5' },
    }));
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LDAPEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(
      wrapper.find('FormGroup[fieldId="AUTH_LDAP_SERVER_URI"]').length
    ).toBe(0);
    expect(
      wrapper.find('FormGroup[fieldId="AUTH_LDAP_5_SERVER_URI"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[fieldId="AUTH_LDAP_5_SERVER_URI"] input').props()
        .value
    ).toEqual('ldap://ldap5.example.com');
  });
});
