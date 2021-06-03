import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import { DashboardAPI } from '../../api';
import Dashboard from './Dashboard';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

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
    await act(async () => {
      pageWrapper
        .find('button[aria-label="Recent Templates list tab"]')
        .simulate('click');
    });
    pageWrapper.update();
    expect(pageWrapper.find('TemplateList').length).toBe(1);
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
