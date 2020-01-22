import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockDetails from './data.host.json';
import Host from './Host';

jest.mock('@api');

describe('<Host />', () => {
  let wrapper;
  let history;

  HostsAPI.readDetail.mockResolvedValue({
    data: { ...mockDetails },
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders succesfully', async () => {
    history = createMemoryHistory({
      initialEntries: ['/hosts/1/edit'],
    });

    await act(async () => {
      wrapper = mountWithContexts(<Host setBreadcrumb={() => {}} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Host').length).toBe(1);
  });

  test('should render "Back to Hosts" tab when navigating from inventories', async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/1'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Host setBreadcrumb={() => {}} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(
      wrapper
        .find('RoutedTabs li')
        .first()
        .text()
    ).toBe('Back to Hosts');
  });

  test('should show content error when api throws error on initial render', async () => {
    HostsAPI.readDetail.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(<Host setBreadcrumb={() => {}} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    history = createMemoryHistory({
      initialEntries: ['/hosts/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Host setBreadcrumb={() => {}} />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
