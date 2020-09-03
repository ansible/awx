import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import { InstanceGroupsAPI } from '../../api';

import ContainerGroup from './ContainerGroup';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    url: '/instance_groups/container_group',
  }),
  useParams: () => ({ id: 42 }),
}));

describe('<ContainerGroup/>', () => {
  let wrapper;
  test('should render details properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<ContainerGroup setBreadcrumb={() => {}} />);
    });
    wrapper.update();
    expect(wrapper.find('ContainerGroup').length).toBe(1);
    expect(InstanceGroupsAPI.readDetail).toBeCalledWith(42);
  });

  test('should render expected tabs', async () => {
    const expectedTabs = ['Back to instance groups', 'Details', 'Jobs'];
    await act(async () => {
      wrapper = mountWithContexts(<ContainerGroup setBreadcrumb={() => {}} />);
    });
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/instance_groups/container_group/42/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ContainerGroup setBreadcrumb={() => {}} />, {
        context: {
          router: {
            history,
          },
        },
      });
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
