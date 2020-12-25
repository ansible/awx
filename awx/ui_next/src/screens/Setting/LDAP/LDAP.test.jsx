import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../../api';
import LDAP from './LDAP';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<LDAP />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
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
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('LDAPDetail').length).toBe(1);
  });

  test('should render ldap edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/ldap/default/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<LDAP />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
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
