import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import { InventoriesAPI, CredentialTypesAPI } from '@api';
import InventoryAdd from './InventoryAdd';

jest.mock('@api');

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
  test('handleSubmit should call the api', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);

    wrapper.update();
    await act(async () => {
      wrapper.find('InventoryForm').prop('handleSubmit')({
        name: 'Foo',
        id: 1,
        organization: 2,
      });
    });

    expect(InventoriesAPI.create).toHaveBeenCalledTimes(1);
  });
  test('handleCancel should return the user back to the inventories list', async () => {
    await waitForElement(wrapper, 'isLoading', el => el.length === 0);
    wrapper.find('CardCloseButton').simulate('click');
    expect(history.location.pathname).toEqual('/inventories');
  });
});
