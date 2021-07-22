import React from 'react';
import { act } from 'react-dom/test-utils';

import { DashboardAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import DashboardGraph from './DashboardGraph';

jest.mock('../../api');

describe('<DashboardGraph/>', () => {
  let pageWrapper;
  let graphRequest;

  beforeEach(async () => {
    await act(async () => {
      DashboardAPI.read.mockResolvedValue({});
      graphRequest = DashboardAPI.readJobGraph;
      graphRequest.mockResolvedValue({});
      pageWrapper = mountWithContexts(<DashboardGraph />);
    });
  });

  test('renders month-based/all job type chart by default', () => {
    expect(graphRequest).toHaveBeenCalledWith({
      job_type: 'all',
      period: 'month',
    });
  });

  test('should render all three line chart filters with correct number of options', async () => {
    expect(pageWrapper.find('Select[variant="single"]')).toHaveLength(3);
    await act(async () => {
      pageWrapper
        .find('Select[placeholderText="Select job type"]')
        .prop('onToggle')(true);
    });
    pageWrapper.update();
    expect(pageWrapper.find('SelectOption')).toHaveLength(4);
    await act(async () => {
      pageWrapper
        .find('Select[placeholderText="Select job type"]')
        .prop('onToggle')(false);
      pageWrapper
        .find('Select[placeholderText="Select period"]')
        .prop('onToggle')(true);
    });
    pageWrapper.update();
    expect(pageWrapper.find('SelectOption')).toHaveLength(4);
    await act(async () => {
      pageWrapper
        .find('Select[placeholderText="Select period"]')
        .prop('onToggle')(false);
      pageWrapper
        .find('Select[placeholderText="Select status"]')
        .prop('onToggle')(true);
    });
    pageWrapper.update();
    expect(pageWrapper.find('SelectOption')).toHaveLength(3);
  });
});
