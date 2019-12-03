import React from 'react';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '@api';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import HostEdit from './HostEdit';

jest.mock('@api');

describe('<HostEdit />', () => {
  const mockData = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    inventory: 1,
    variables: '---',
    summary_fields: {
      inventory: {
        id: 1,
        name: 'test inventory',
      },
    },
  };

  test('handleSubmit should call api update', () => {
    const wrapper = mountWithContexts(<HostEdit host={mockData} />);

    const updatedHostData = {
      name: 'new name',
      description: 'new description',
      variables: '---\nfoo: bar',
    };
    wrapper.find('HostForm').prop('handleSubmit')(updatedHostData);

    expect(HostsAPI.update).toHaveBeenCalledWith(1, updatedHostData);
  });

  test('should navigate to host detail when cancel is clicked', () => {
    const history = createMemoryHistory({});
    const wrapper = mountWithContexts(<HostEdit host={mockData} />, {
      context: { router: { history } },
    });

    wrapper.find('button[aria-label="Cancel"]').prop('onClick')();

    expect(history.location.pathname).toEqual('/hosts/1/details');
  });
});
