import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import { DashboardAPI } from '../../api';
import Dashboard from './Dashboard';

jest.mock('../../api');

describe('<Dashboard />', () => {
  let pageWrapper;
  let graphRequest;

  beforeEach(async () => {
    await act(async () => {
      DashboardAPI.read.mockResolvedValue({});
      graphRequest = DashboardAPI.readJobGraph;
      graphRequest.mockResolvedValue({});
      pageWrapper = mountWithContexts(<Dashboard />);
    });
  });

  afterEach(() => {
    pageWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(pageWrapper.length).toBe(1);
  });

  test('renders dashboard graph by default', () => {
    expect(pageWrapper.find('LineChart').length).toBe(1);
  });

  test('renders template list when the active tab is changed', async () => {
    expect(pageWrapper.find('DashboardTemplateList').length).toBe(0);
    pageWrapper
      .find('button[aria-label="Recent Templates list tab"]')
      .simulate('click');
    expect(pageWrapper.find('DashboardTemplateList').length).toBe(1);
  });

  test('renders month-based/all job type chart by default', () => {
    expect(graphRequest).toHaveBeenCalledWith({
      job_type: 'all',
      period: 'month',
    });
  });
});
