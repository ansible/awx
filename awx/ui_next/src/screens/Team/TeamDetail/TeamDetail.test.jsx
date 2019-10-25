import React from 'react';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import TeamDetail from './TeamDetail';

jest.mock('@api');

describe('<TeamDetail />', () => {
  const mockTeam = {
    name: 'Foo',
    description: 'Bar',
    created: '2015-07-07T17:21:26.429745Z',
    modified: '2019-08-11T19:47:37.980466Z',
    summary_fields: {
      organization: {
        id: 1,
        name: 'Default',
      },
      user_capabilities: {
        edit: true,
      },
    },
  };
  test('initially renders succesfully', () => {
    mountWithContexts(<TeamDetail team={mockTeam} />);
  });

  test('should render Details', async done => {
    const wrapper = mountWithContexts(<TeamDetail team={mockTeam} />);
    const testParams = [
      { label: 'Name', value: 'Foo' },
      { label: 'Description', value: 'Bar' },
      { label: 'Organization', value: 'Default' },
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
    const wrapper = mountWithContexts(<TeamDetail team={mockTeam} />);
    const editButton = await waitForElement(wrapper, 'TeamDetail Button');
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/teams/undefined/edit');
    done();
  });

  test('should hide edit button for users without edit permission', async done => {
    const readOnlyTeam = { ...mockTeam };
    readOnlyTeam.summary_fields.user_capabilities.edit = false;
    const wrapper = mountWithContexts(<TeamDetail team={readOnlyTeam} />);
    await waitForElement(wrapper, 'TeamDetail');
    expect(wrapper.find('TeamDetail Button').length).toBe(0);
    done();
  });
});
