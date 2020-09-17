import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../../api';
import SAML from './SAML';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<SAML />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render SAML details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/saml/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<SAML />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('SAMLDetail').length).toBe(1);
  });

  test('should render SAML edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/saml/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<SAML />, {
        context: { router: { history } },
      });
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
