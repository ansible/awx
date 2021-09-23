import React from 'react';
import { act } from 'react-dom/test-utils';

import { MetricsAPI, InstancesAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Metrics from './Metrics';

jest.mock('../../api/models/Instances');
jest.mock('../../api/models/Metrics');

describe('<Metrics/>', () => {
  let wrapper;
  beforeEach(async () => {
    InstancesAPI.read.mockResolvedValue({
      data: {
        results: [
          { hostname: 'instance 1', node_type: 'control' },
          { hostname: 'instance 2', node_type: 'hybrid' },
          { hostname: 'receptor', node_type: 'execution' },
        ],
      },
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
    await act(async () => {
      wrapper = mountWithContexts(<Metrics />);
    });
  });
  afterEach(() => {
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
    await act(async () => {
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

  test('should not include receptor instances', async () => {
    await act(async () => {
      wrapper.find('Select[ouiaId="Instance-select"]').prop('onToggle')(true);
    });
    wrapper.update();
    expect(wrapper.find('SelectOption[value="receptor"]')).toHaveLength(0);
    expect(
      wrapper.find('Select[ouiaId="Instance-select"]').find('SelectOption')
    ).toHaveLength(3);
  });
});
