import React from 'react';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import HostDetail from './HostDetail';

jest.mock('@api');

describe('<HostDetail />', () => {
  const mockHost = {
    id: 1,
    name: 'Foo',
    description: 'Bar',
    inventory: 1,
    created: '2015-07-07T17:21:26.429745Z',
    modified: '2019-08-11T19:47:37.980466Z',
    variables: '---',
    summary_fields: {
      inventory: {
        id: 1,
        name: 'test inventory',
      },
      user_capabilities: {
        edit: true,
      },
    },
  };

  test('initially renders succesfully', () => {
    mountWithContexts(<HostDetail host={mockHost} />);
  });

  test('should render Details', async done => {
    const wrapper = mountWithContexts(<HostDetail host={mockHost} />);
    const testParams = [
      { label: 'Name', value: 'Foo' },
      { label: 'Description', value: 'Bar' },
      { label: 'Inventory', value: 'test inventory' },
      { label: 'Created', value: '7/7/2015, 5:21:26 PM' },
      { label: 'Last Modified', value: '8/11/2019, 7:47:37 PM' },
    ];
    // eslint-disable-next-line no-restricted-syntax
    for (const { label, value } of testParams) {
      // eslint-disable-next-line no-await-in-loop
      const detail = await waitForElement(wrapper, `Detail[label="${label}"]`);
      expect(detail.find('dt').text()).toBe(label);
      expect(detail.find('dd').text()).toBe(value);
    }
    done();
  });

  test('should show edit button for users with edit permission', async done => {
    const wrapper = mountWithContexts(<HostDetail host={mockHost} />);
    const editButton = await waitForElement(wrapper, 'HostDetail Button');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/hosts/1/edit');
    done();
  });

  test('should hide edit button for users without edit permission', async done => {
    const readOnlyHost = { ...mockHost };
    readOnlyHost.summary_fields.user_capabilities.edit = false;
    const wrapper = mountWithContexts(<HostDetail host={readOnlyHost} />);
    await waitForElement(wrapper, 'HostDetail');
    expect(wrapper.find('HostDetail Button').length).toBe(0);
    done();
  });
});
