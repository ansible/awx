import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import HostAdd from './HostAdd';
import { HostsAPI } from '@api';

jest.mock('@api');

describe('<HostAdd />', () => {
  let wrapper;
  let history;

  const hostData = {
    name: 'new name',
    description: 'new description',
    inventory: 1,
    variables: '---\nfoo: bar',
  };

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/hosts/1/add'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<HostAdd />, {
        context: { router: { history } },
      });
    });
  });

  test('handleSubmit should post to api', async () => {
    HostsAPI.create.mockResolvedValueOnce({
      data: {
        ...hostData,
        id: 5,
      },
    });
    await act(async () => {
      wrapper.find('HostForm').prop('handleSubmit')(hostData);
    });
    expect(HostsAPI.create).toHaveBeenCalledWith(hostData);
  });

  test('should navigate to hosts list when cancel is clicked', async () => {
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(history.location.pathname).toEqual('/hosts');
  });

  test('successful form submission should trigger redirect', async () => {
    HostsAPI.create.mockResolvedValueOnce({
      data: {
        ...hostData,
        id: 5,
      },
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await act(async () => {
      wrapper.find('HostForm').invoke('handleSubmit')(hostData);
    });
    expect(history.location.pathname).toEqual('/hosts/5/details');
  });
});
