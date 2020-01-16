import React from 'react';
import { Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import { InventoriesAPI } from '@api';
import InventoryHostAdd from './InventoryHostAdd';

jest.mock('@api');

describe('<InventoryHostAdd />', () => {
  let wrapper;
  let history;

  const mockHostData = {
    name: 'new name',
    description: 'new description',
    inventory: 1,
    variables: '---\nfoo: bar',
  };

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/inventories/inventory/1/hosts/add'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <Route
          path="/inventories/inventory/:id/hosts/add"
          component={() => <InventoryHostAdd />}
        />,
        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('handleSubmit should post to api', async () => {
    InventoriesAPI.createHost.mockResolvedValue({
      data: { ...mockHostData },
    });

    await act(async () => {
      wrapper.find('FormField[id="host-name"] input').simulate('change', {
        target: { value: 'new name', name: 'name' },
      });
      wrapper
        .find('FormField[id="host-description"] input')
        .simulate('change', {
          target: { value: 'new description', name: 'description' },
        });
      wrapper.update();
      await sleep(0);
      wrapper.find('FormActionGroup').invoke('onSubmit')();
    });
    wrapper.update();
    expect(InventoriesAPI.createHost).toHaveBeenCalledWith('1', {
      name: 'new name',
      description: 'new description',
      variables: '---\n',
    });
  });

  test('handleSubmit should throw an error', async () => {
    InventoriesAPI.createHost.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper.find('FormField[id="host-name"] input').simulate('change', {
        target: { value: 'new name', name: 'name' },
      });
      wrapper
        .find('FormField[id="host-description"] input')
        .simulate('change', {
          target: { value: 'new description', name: 'description' },
        });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('form').simulate('submit');
    });
    wrapper.update();
    expect(wrapper.find('InventoryHostAdd .formSubmitError').length).toBe(1);
  });

  test('should navigate to inventory hosts list when cancel is clicked', async () => {
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(history.location.pathname).toEqual('/inventories/inventory/1/hosts');
  });
});
