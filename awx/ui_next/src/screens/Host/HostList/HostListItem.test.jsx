import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import HostsListItem from './HostListItem';

let toggleHost;

const mockHost = {
  id: 1,
  name: 'Host 1',
  url: '/api/v2/hosts/1',
  inventory: 1,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'Inv 1',
    },
    user_capabilities: {
      edit: true,
    },
  },
};

describe('<HostsListItem />', () => {
  beforeEach(() => {
    toggleHost = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <HostsListItem
        isSelected={false}
        detailUrl="/host/1"
        onSelect={() => {}}
        host={mockHost}
        toggleHost={toggleHost}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
  test('edit button hidden from users without edit capabilities', () => {
    const copyMockHost = Object.assign({}, mockHost);
    copyMockHost.summary_fields.user_capabilities.edit = false;
    const wrapper = mountWithContexts(
      <HostsListItem
        isSelected={false}
        detailUrl="/host/1"
        onSelect={() => {}}
        host={copyMockHost}
        toggleHost={toggleHost}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
  test('handles toggle click when host is enabled', () => {
    const wrapper = mountWithContexts(
      <HostsListItem
        isSelected={false}
        detailUrl="/host/1"
        onSelect={() => {}}
        host={mockHost}
        toggleHost={toggleHost}
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleHost).toHaveBeenCalledWith(mockHost);
  });

  test('handles toggle click when host is disabled', () => {
    const wrapper = mountWithContexts(
      <HostsListItem
        isSelected={false}
        detailUrl="/host/1"
        onSelect={() => {}}
        host={mockHost}
        toggleHost={toggleHost}
      />
    );
    wrapper
      .find('Switch')
      .first()
      .find('input')
      .simulate('change');
    expect(toggleHost).toHaveBeenCalledWith(mockHost);
  });
});
