import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import HostAdd from './HostAdd';
import { HostsAPI } from '@api';

jest.mock('@api');

describe('<HostAdd />', () => {
  test('handleSubmit should post to api', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostAdd />);
    });
    const updatedHostData = {
      name: 'new name',
      description: 'new description',
      inventory: 1,
      variables: '---\nfoo: bar',
    };
    wrapper.find('HostForm').prop('handleSubmit')(updatedHostData);
    expect(HostsAPI.create).toHaveBeenCalledWith(updatedHostData);
  });

  test('should navigate to hosts list when cancel is clicked', async () => {
    const history = createMemoryHistory({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostAdd />, {
        context: { router: { history } },
      });
    });
    wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    expect(history.location.pathname).toEqual('/hosts');
  });

  test('successful form submission should trigger redirect', async () => {
    const history = createMemoryHistory({});
    const hostData = {
      name: 'new name',
      description: 'new description',
      inventory: 1,
      variables: '---\nfoo: bar',
    };
    HostsAPI.create.mockResolvedValueOnce({
      data: {
        id: 5,
        ...hostData,
      },
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<HostAdd />, {
        context: { router: { history } },
      });
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await wrapper.find('HostForm').invoke('handleSubmit')(hostData);
    expect(history.location.pathname).toEqual('/hosts/5');
  });
});
