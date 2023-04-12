import React from 'react';
import { act } from 'react-dom/test-utils';
import { DashboardAPI, RootAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Dashboard from './Dashboard';

jest.mock('../../api');

describe('<Dashboard />', () => {
  let pageWrapper;
  let graphRequest;

  beforeEach(async () => {
    await act(async () => {
      DashboardAPI.read.mockResolvedValue({});
      RootAPI.readAssetVariables.mockResolvedValue({
        data: {
          BRAND_NAME: 'AWX',
        },
      });
      graphRequest = DashboardAPI.readJobGraph;
      graphRequest.mockResolvedValue({});
      pageWrapper = mountWithContexts(<Dashboard />);
    });
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });

  test('renders dashboard graph by default', () => {
    expect(pageWrapper.find('LineChart').length).toBe(1);
  });

  test('renders template list when the active tab is changed', async () => {
    expect(pageWrapper.find('DashboardTemplateList').length).toBe(0);
    await act(async () => {
      pageWrapper
        .find('button[aria-label="Recent Templates list tab"]')
        .simulate('click');
    });
    pageWrapper.update();
    expect(pageWrapper.find('TemplateList').length).toBe(1);
  });
});
