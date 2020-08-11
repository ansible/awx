import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import { sleep } from '../../../../testUtils/testUtils';

import { InventoriesAPI, CredentialTypesAPI } from '../../../api';
import InventoryAdd from './InventoryAdd';

jest.mock('../../../api');

CredentialTypesAPI.read.mockResolvedValue({
  data: {
    results: [
      {
        id: 14,
        name: 'insights',
      },
    ],
  },
});
InventoriesAPI.create.mockResolvedValue({ data: { id: 13 } });

describe('<InventoryAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory({ initialEntries: ['/inventories'] });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryAdd />, {
        context: { router: { history } },
      });
    });
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('Initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('handleSubmit should call the api and redirect to details page', async () => {
    const instanceGroups = [
      { name: 'Bizz', id: 1 },
      { name: 'Buzz', id: 2 },
    ];
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);

    await act(async () => {
      wrapper.find('InventoryForm').prop('onSubmit')({
        name: 'new Foo',
        organization: { id: 2 },
        insights_credential: { id: 47 },
        instanceGroups,
      });
    });
    await sleep(1);
    expect(InventoriesAPI.create).toHaveBeenCalledWith({
      name: 'new Foo',
      organization: 2,
      insights_credential: 47,
    });
    instanceGroups.map(IG =>
      expect(InventoriesAPI.associateInstanceGroup).toHaveBeenCalledWith(
        13,
        IG.id
      )
    );
    expect(history.location.pathname).toBe('/inventories/inventory/13/details');
  });

  test('handleCancel should return the user back to the inventories list', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);
    await act(async () => {
      wrapper.find('Button[aria-label="Cancel"]').simulate('click');
    });
    expect(history.location.pathname).toEqual('/inventories');
  });
});
