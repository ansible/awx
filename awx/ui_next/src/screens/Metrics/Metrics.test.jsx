import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Metrics from './Metrics';
import { MetricsAPI, InstancesAPI } from '../../api';

jest.mock('../../api/models/Instances');
jest.mock('../../api/models/Metrics');
InstancesAPI.read.mockResolvedValue({
  data: { results: [{ hostname: 'instance 1' }, { hostname: 'instance 2' }] },
});
MetricsAPI.read.mockResolvedValue({
  data: {
    metric1: {
      helptext: 'metric 1 help text',
      samples: [{ labels: { node: 'metric 1' }, value: 20 }],
    },
    metric2: {
      helptext: 'metric 2 help text',
      samples: [{ labels: { node: 'metric 2' }, value: 10 }],
    },
  },
});

describe('<Metrics/>', () => {
  let wrapper;
  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Metrics />);
    });
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('should mound properly', () => {
    expect(wrapper.find('Metrics').length).toBe(1);
    expect(wrapper.find('EmptyStateBody').length).toBe(1);
    expect(wrapper.find('ChartLine').length).toBe(0);
  });
  test('should render chart after selecting metric and instance', async () => {
    await act(async () => {
      wrapper.find('Select[ouiaId="Instance-select"]').prop('onToggle')(true);
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('SelectOption[value="instance 1"]')
        .find('button')
        .prop('onClick')({}, 'instance 1');
    });
    wrapper.update();
    await act(() => {
      wrapper.find('Select[ouiaId="Metric-select"]').prop('onToggle')(true);
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('SelectOption[value="metric1"]')
        .find('button')
        .prop('onClick')({}, 'metric1');
    });
    wrapper.update();
    expect(MetricsAPI.read).toBeCalledWith({
      subsystemonly: 1,
      format: 'json',
      metric: 'metric1',
      node: 'instance 1',
    });
  });
});
