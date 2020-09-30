import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { SettingsAPI } from '../../../api';
import TACACS from './TACACS';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {},
});

describe('<TACACS />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render TACACS+ details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<TACACS />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('TACACSDetail').length).toBe(1);
  });

  test('should render TACACS+ edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<TACACS />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('TACACSEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<TACACS />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
