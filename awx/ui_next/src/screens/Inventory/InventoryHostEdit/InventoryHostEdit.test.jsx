import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '../../../api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryHostEdit from './InventoryHostEdit';
import mockHost from '../shared/data.host.json';

jest.mock('../../../api');

describe('<InventoryHostEdit />', () => {
  let wrapper;
  let history;

  const updatedHostData = {
    name: 'new name',
    description: 'new description',
    variables: '---\nfoo: bar',
  };

  beforeAll(async () => {
    history = createMemoryHistory();
    await act(async () => {
      wrapper = mountWithContexts(
        <InventoryHostEdit host={mockHost} inventory={{ id: 123 }} />,
        {
          context: { router: { history } },
        }
      );
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
    wrapper.unmount();
  });

  test('handleSubmit should call api update', async () => {
    await act(async () => {
      wrapper.find('HostForm').prop('handleSubmit')(updatedHostData);
    });
    expect(HostsAPI.update).toHaveBeenCalledWith(2, updatedHostData);
  });

  test('should navigate to inventory host detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/123/hosts/2/details'
    );
  });

  test('should navigate to inventory host detail after successful submission', async () => {
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(updatedHostData);
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/123/hosts/2/details'
    );
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    HostsAPI.update.mockImplementationOnce(() => Promise.reject(error));
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(mockHost);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
