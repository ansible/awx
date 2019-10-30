import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import HostAdd from './HostAdd';
import { HostsAPI } from '@api';

jest.mock('@api');

describe('<HostAdd />', () => {
  test('handleSubmit should post to api', () => {
    const wrapper = mountWithContexts(<HostAdd />);
    const updatedHostData = {
      name: 'new name',
      description: 'new description',
      inventory: 1,
      variables: '---\nfoo: bar',
    };
    wrapper.find('HostForm').prop('handleSubmit')(updatedHostData);
    expect(HostsAPI.create).toHaveBeenCalledWith(updatedHostData);
  });

  test('should navigate to hosts list when cancel is clicked', () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<HostAdd />, {
      context: { router: { history } },
    });
    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();
    expect(history.location.pathname).toEqual('/hosts');
  });

  test('should navigate to hosts list when close (x) is clicked', () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<HostAdd />, {
      context: { router: { history } },
    });
    wrapper.find('button[aria-label="Close"]').prop('onClick')();
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
    const wrapper = mountWithContexts(<HostAdd />, {
      context: { router: { history } },
    });
    await waitForElement(wrapper, 'button[aria-label="Save"]');
    await wrapper.find('HostForm').prop('handleSubmit')(hostData);
    expect(history.location.pathname).toEqual('/hosts/5');
  });
});
