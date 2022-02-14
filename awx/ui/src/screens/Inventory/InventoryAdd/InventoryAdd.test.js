import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { LabelsAPI, InventoriesAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';

import InventoryAdd from './InventoryAdd';

jest.mock('../../../api');

describe('<InventoryAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({ initialEntries: ['/inventories'] });
    LabelsAPI.read.mockResolvedValue({ data: { results: [] } });
    InventoriesAPI.create.mockResolvedValue({ data: { id: 13 } });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryAdd />, {
        context: { router: { history } },
      });
    });
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('handleSubmit should call the api and redirect to details page', async () => {
    const instanceGroups = [
      { name: 'Bizz', id: 1 },
      { name: 'Buzz', id: 2 },
    ];
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);

    await act(async () => {
      wrapper.find('InventoryForm').prop('onSubmit')({
        name: 'new Foo',
        organization: { id: 2 },
        instanceGroups,
        labels: [{ name: 'label' }],
      });
    });
    expect(InventoriesAPI.create).toHaveBeenCalledWith({
      name: 'new Foo',
      organization: 2,
      labels: [{ name: 'label' }],
    });
    expect(InventoriesAPI.associateLabel).toBeCalledWith(
      13,
      { name: 'label' },
      2
    );
    instanceGroups.map((IG) =>
      expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledWith(
        13,
        IG.id
      )
    );
    expect(history.location.pathname).toBe('/inventories/inventory/13/details');
  });

  test('handleCancel should return the user back to the inventories list', async () => {
    await waitForElement(wrapper, 'isLoading', (el) => el.length === 0);
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual('/inventories');
  });
});
