import React from 'react';
import { act } from 'react-dom/test-utils';
import { HostMetricsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import HostMetrics from './HostMetrics';

jest.mock('../../api');

const mockHostMetrics = [
  {
    hostname: 'Host name',
    first_automation: 'now',
    last_automation: 'now',
    automated_counter: 1,
    used_in_inventories: 1,
    deleted_counter: 1,
    id: 1,
    url: '',
  },
];

function waitForLoaded(wrapper) {
  return waitForElement(
    wrapper,
    'HostList',
    (el) => el.find('ContentLoading').length === 0
  );
}

describe('<HostMetrics />', () => {
  beforeEach(() => {
    HostMetricsAPI.read.mockResolvedValue({
      data: {
        count: mockHostMetrics.length,
        results: mockHostMetrics,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders successfully', async () => {
    await act(async () => {
      mountWithContexts(
        <HostMetrics
          match={{ path: '/hosts', url: '/hosts' }}
          location={{ search: '', pathname: '/hosts' }}
        />
      );
    });
  });

  test('HostMetrics are retrieved from the api and the components finishes loading', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostMetrics />);
    });
    await waitForLoaded(wrapper);

    expect(HostMetricsAPI.read).toHaveBeenCalled();
    expect(wrapper.find('HostMetricsListItem')).toHaveLength(1);
  });
});
