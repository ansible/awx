import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { HostsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventoryHostAdd from './InventoryHostAdd';
import mockHost from '../shared/data.host.json';

jest.mock('../../../api');

describe('<InventoryHostAdd />', () => {
  let wrapper;
  let history;

  beforeEach(async () => {
    history = createMemoryHistory();
    HostsAPI.create.mockResolvedValue({
      data: {
        ...mockHost,
      },
    });
    await act(async () => {
      wrapper = mountWithContexts(<InventoryHostAdd inventory={{ id: 3 }} />, {
        context: { router: { history } },
      });
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('handleSubmit should post to api', async () => {
    await act(async () => {
      wrapper.find('HostForm').prop('handleSubmit')(mockHost);
    });
    expect(HostsAPI.create).toHaveBeenCalledWith(mockHost);
  });

  test('should navigate to hosts list when cancel is clicked', () => {
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(history.location.pathname).toEqual('/inventories/inventory/3/hosts');
  });

  test('successful form submission should trigger redirect', async () => {
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(mockHost);
    });
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(history.location.pathname).toEqual(
      '/inventories/inventory/3/hosts/2/details'
    );
  });

  test('failed form submission should show an error message', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    HostsAPI.create.mockImplementationOnce(() => Promise.reject(error));
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(mockHost);
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
  });
});
