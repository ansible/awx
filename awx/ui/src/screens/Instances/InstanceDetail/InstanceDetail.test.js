import React from 'react';
import { act } from 'react-dom/test-utils';
import * as ConfigContext from 'contexts/Config';
import useDebounce from 'hooks/useDebounce';
import { InstancesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import InstanceDetail from './InstanceDetail';

jest.mock('../../../api');
jest.mock('../../../hooks/useDebounce');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));

describe('<InstanceDetail/>', () => {
  let wrapper;
  beforeEach(() => {
    useDebounce.mockImplementation((fn) => fn);

    InstancesAPI.readDetail.mockResolvedValue({
      data: {
        related: {},
        id: 1,
        type: 'instance',
        url: '/api/v2/instances/1/',
        uuid: '00000000-0000-0000-0000-000000000000',
        hostname: 'awx_1',
        created: '2021-09-08T17:10:34.484569Z',
        modified: '2021-09-09T13:55:44.219900Z',
        last_seen: '2021-09-09T20:20:31.623148Z',
        last_health_check: '2021-09-09T20:20:31.623148Z',
        errors: '',
        capacity_adjustment: '1.00',
        version: '19.1.0',
        capacity: 38,
        consumed_capacity: 0,
        percent_capacity_remaining: 100.0,
        jobs_running: 0,
        jobs_total: 0,
        cpu: 8,
        memory: 6232231936,
        cpu_capacity: 32,
        mem_capacity: 38,
        enabled: true,
        managed_by_policy: true,
        node_type: 'execution',
        node_state: 'ready',
        health_check_pending: false,
      },
    });
    InstancesAPI.readInstanceGroup.mockResolvedValue({
      data: {
        results: [
          {
            id: 1,
            name: 'Foo',
          },
        ],
      },
    });
    InstancesAPI.readHealthCheckDetail.mockResolvedValue({
      data: {
        uuid: '00000000-0000-0000-0000-000000000000',
        hostname: 'awx_1',
        version: '19.1.0',
        last_health_check: '2021-09-10T16:16:19.729676Z',
        errors: '',
        cpu: 8,
        memory: 6232231936,
        cpu_capacity: 32,
        mem_capacity: 38,
        capacity: 38,
      },
    });
  });
  afterEach(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });
  test('Should render proper data', async () => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_superuser: true },
    }));
    await act(async () => {
      wrapper = mountWithContexts(<InstanceDetail setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('InstanceDetail')).toHaveLength(1);

    expect(InstancesAPI.readDetail).toBeCalledWith(1);
    expect(InstancesAPI.readHealthCheckDetail).toBeCalledWith(1);
    expect(
      wrapper.find("Button[ouiaId='health-check-button']").prop('isDisabled')
    ).toBe(false);
  });

  test('should calculate number of forks when slide changes', async () => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_superuser: true },
    }));
    await act(async () => {
      wrapper = mountWithContexts(<InstanceDetail setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);

    expect(wrapper.find('InstanceDetail').length).toBe(1);
    expect(wrapper.find('div[data-cy="number-forks"]').text()).toContain(
      '38 forks'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(4);
    });

    wrapper.update();

    expect(wrapper.find('div[data-cy="number-forks"]').text()).toContain(
      '56 forks'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(0);
    });
    wrapper.update();
    expect(wrapper.find('div[data-cy="number-forks"]').text()).toContain(
      '32 forks'
    );

    await act(async () => {
      wrapper.find('Slider').prop('onChange')(0.5);
    });
    wrapper.update();
    expect(wrapper.find('div[data-cy="number-forks"]').text()).toContain(
      '35 forks'
    );
  });

  test('buttons should be disabled', async () => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_system_auditor: true },
    }));
    await act(async () => {
      wrapper = mountWithContexts(<InstanceDetail setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);

    expect(
      wrapper.find("Button[ouiaId='health-check-button']").prop('isDisabled')
    ).toBe(true);
  });

  test('should display instance toggle', async () => {
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_system_auditor: true },
    }));
    await act(async () => {
      wrapper = mountWithContexts(<InstanceDetail setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('InstanceToggle').length).toBe(1);
  });

  test('Should handle api error for health check', async () => {
    InstancesAPI.healthCheck.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/instances/1/health_check',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    jest.spyOn(ConfigContext, 'useConfig').mockImplementation(() => ({
      me: { is_superuser: true },
    }));
    await act(async () => {
      wrapper = mountWithContexts(<InstanceDetail setBreadcrumb={() => {}} />);
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(
      wrapper.find("Button[ouiaId='health-check-button']").prop('isDisabled')
    ).toBe(false);
    await act(async () => {
      wrapper.find("Button[ouiaId='health-check-button']").prop('onClick')();
    });
    expect(InstancesAPI.healthCheck).toBeCalledWith(1);
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(1);
    expect(wrapper.find('ErrorDetail')).toHaveLength(1);
  });
});
