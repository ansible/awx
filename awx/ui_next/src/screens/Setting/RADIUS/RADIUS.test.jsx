import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../contexts/Settings';
import { SettingsAPI } from '../../../api';
import mockAllOptions from '../shared/data.allSettingOptions.json';
import RADIUS from './RADIUS';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    RADIUS_SERVER: 'radius.example.org',
    RADIUS_PORT: 1812,
    RADIUS_SECRET: '$encrypted$',
  },
});

describe('<RADIUS />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render RADIUS details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/radius/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <RADIUS />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('RADIUSDetail').length).toBe(1);
  });

  test('should render RADIUS edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/radius/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <RADIUS />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    expect(wrapper.find('RADIUSEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/radius/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<RADIUS />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
