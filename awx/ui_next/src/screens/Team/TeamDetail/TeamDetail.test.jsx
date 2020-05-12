import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import TeamDetail from './TeamDetail';
import { TeamsAPI } from '../../../api';

jest.mock('../../../api');

describe('<TeamDetail />', () => {
  let wrapper;
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
        delete: true,
      },
    },
  };

  beforeEach(async () => {
    wrapper = mountWithContexts(<TeamDetail team={mockTeam} />);
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders succesfully', async () => {
    await waitForElement(wrapper, 'TeamDetail');
  });

  test('should render Details', async () => {
    const testParams = [
      { label: 'Name', value: 'Foo' },
      { label: 'Description', value: 'Bar' },
      { label: 'Organization', value: 'Default' },
      { label: 'Created', value: '7/7/2015, 5:21:26 PM' },
      { label: 'Last Modified', value: '8/11/2019, 7:47:37 PM' },
    ];
    for (let i = 0; i < testParams.length; i++) {
      const { label, value } = testParams[i];
      // eslint-disable-next-line no-await-in-loop
      const detail = await waitForElement(wrapper, `Detail[label="${label}"]`);
      expect(detail.find('dt').text()).toBe(label);
      expect(detail.find('dd').text()).toBe(value);
    }
  });

  test('should show edit button for users with edit permission', async () => {
    const editButton = await waitForElement(
      wrapper,
      'TeamDetail Button[aria-label="Edit"]'
    );
    expect(editButton.text()).toEqual('Edit');
    expect(editButton.prop('to')).toBe('/teams/undefined/edit');
  });

  test('should hide edit button for users without edit permission', async () => {
    const readOnlyTeam = { ...mockTeam };
    readOnlyTeam.summary_fields.user_capabilities.edit = false;
    wrapper = mountWithContexts(<TeamDetail team={readOnlyTeam} />);
    await waitForElement(wrapper, 'TeamDetail');
    expect(wrapper.find('TeamDetail Button[aria-label="Edit"]').length).toBe(0);
  });

  test('expected api call is made for delete', async () => {
    await waitForElement(wrapper, 'TeamDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    expect(TeamsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('Error dialog shown for failed deletion', async () => {
    TeamsAPI.destroy.mockImplementationOnce(() => Promise.reject(new Error()));
    wrapper = mountWithContexts(<TeamDetail team={mockTeam} />);
    await waitForElement(wrapper, 'TeamDetail Button[aria-label="Delete"]');
    await act(async () => {
      wrapper.find('DeleteButton').invoke('onConfirm')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 1
    );
    await act(async () => {
      wrapper.find('Modal[title="Error!"]').invoke('onClose')();
    });
    await waitForElement(
      wrapper,
      'Modal[title="Error!"]',
      el => el.length === 0
    );
  });
});
