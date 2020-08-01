import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { GroupsAPI } from '../../../api';

import InventoryGroup from './InventoryGroup';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    groupId: 2,
  }),
}));

GroupsAPI.readDetail.mockResolvedValue({
  data: {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    variables: 'bizz: buzz',
    summary_fields: {
      inventory: { id: 1 },
      created_by: { id: 1, username: 'Athena' },
      modified_by: { id: 1, username: 'Apollo' },
    },
    created: '2020-04-25T01:23:45.678901Z',
    modified: '2020-04-25T01:23:45.678901Z',
  },
});

describe('<InventoryGroup />', () => {
  let wrapper;
  let history;
  const inventory = { id: 1, name: 'Foo' };

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/1/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/inventories/inventory/:id/groups">
          <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />
        </Route>,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('renders successfully', async () => {
    expect(wrapper.length).toBe(1);
  });

  test('expect all tabs to exist, including Back to Groups', async () => {
    expect(
      wrapper.find('button[link="/inventories/inventory/1/groups"]').length
    ).toBe(1);
    expect(wrapper.find('button[aria-label="Details"]').length).toBe(1);
    expect(wrapper.find('button[aria-label="Related Groups"]').length).toBe(1);
    expect(wrapper.find('button[aria-label="Hosts"]').length).toBe(1);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/groups/1/foobar'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryGroup setBreadcrumb={() => {}} inventory={inventory} />,
        { context: { router: { history } } }
      );
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });

  test('should show content error when api throws error on initial render', async () => {
    GroupsAPI.readDetail.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(<InventoryGroup inventory={inventory} />);
    });
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
