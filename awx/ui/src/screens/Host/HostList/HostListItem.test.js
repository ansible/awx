import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import HostsListItem from './HostListItem';

const mockHost = {
  id: 1,
  name: 'Host 1',
  url: '/api/v2/hosts/1',
  description: 'Buzz',
  inventory: 1,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Inv 1',
    },
    user_capabilities: {
      edit: true,
    },
    recent_jobs: [],
  },
};

describe('<HostsListItem />', () => {
  let wrapper;

  beforeEach(() => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <HostsListItem
            isSelected={false}
            detailUrl="/host/1"
            onSelect={() => {}}
            host={mockHost}
          />
        </tbody>
      </table>
    );
  });

  test('should display expected details', () => {
    expect(wrapper.find('HostListItem').length).toBe(1);
    expect(wrapper.find('Td[dataLabel="Name"]').find('Link').prop('to')).toBe(
      '/host/1'
    );
    expect(wrapper.find('Td[dataLabel="Description"]').text()).toBe('Buzz');
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const copyMockHost = { ...mockHost };
    copyMockHost.summary_fields.user_capabilities.edit = false;
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <HostsListItem
            isSelected={false}
            detailUrl="/host/1"
            onSelect={() => {}}
            host={copyMockHost}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });

  test('should display host toggle', () => {
    expect(wrapper.find('HostToggle').length).toBe(1);
  });
});
