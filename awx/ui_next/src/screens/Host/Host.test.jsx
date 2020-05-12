import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import mockHost from './data.host.json';
import Host from './Host';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/hosts/1',
    params: { id: 1 },
  }),
}));

HostsAPI.readDetail.mockResolvedValue({
  data: { ...mockHost },
});

describe('<Host />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(<Host setBreadcrumb={() => {}} />);
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('should render expected tabs', async () => {
    const expectedTabs = ['Details', 'Facts', 'Groups', 'Completed Jobs'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
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
