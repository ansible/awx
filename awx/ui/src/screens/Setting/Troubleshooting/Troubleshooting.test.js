import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import mockJobSettings from '../shared/data.jobSettings.json';
import Jobs from './Troubleshooting';
import Troubleshooting from './Troubleshooting';

jest.mock('../../../api');

describe('<Troubleshooting />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockJobSettings,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should render troubleshooting details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/troubleshooting/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Jobs />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('TroubleshootingDetail').length).toBe(1);
  });

  test('should render troubleshooting edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/troubleshooting/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Jobs />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('TroubleshootingEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/troubleshooting/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Troubleshooting />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
