import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import { SettingsProvider } from 'contexts/Settings';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import mockLDAP from '../shared/data.ldapSettings.json';
import LDAP from './LDAP';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({ data: mockLDAP });

describe('<LDAP />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render ldap details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ldap/'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<LDAP />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('LDAPDetail').length).toBe(1);
  });

  test('should render ldap edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ldap/default/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <LDAP />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('LDAPEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ldap/foo/bar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<LDAP />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
