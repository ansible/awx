import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../../api';
import AzureAD from './AzureAD';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<AzureAD />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render azure details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<AzureAD />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('AzureADDetail').length).toBe(1);
  });

  test('should render azure edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<AzureAD />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('AzureADEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/azure/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<AzureAD />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
