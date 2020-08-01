import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import HostDetail from './HostDetail';
import { HostsAPI } from '../../../api';

import mockHost from '../data.host.json';

jest.mock('../../../api');

describe('<HostDetail />', () => {
  let wrapper;

  describe('User has edit permissions', () => {
    beforeAll(() => {
      wrapper = mountWithContexts(<HostDetail host={mockHost} />);
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('should render Details', async () => {
      function assertDetail(label, value) {
        expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
        expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
      }

      assertDetail('Name', 'localhost');
      assertDetail('Description', 'a good description');
      assertDetail('Inventory', 'Mikes Inventory');
      assertDetail('Created', '10/28/2019, 9:26:54 PM');
      assertDetail('Last Modified', '10/29/2019, 8:18:41 PM');
    });

    test('should show edit button for users with edit permission', () => {
      const editButton = wrapper.find('Button[aria-label="edit"]');
      expect(editButton.text()).toEqual('Edit');
      expect(editButton.prop('to')).toBe('/hosts/2/edit');
    });

    test('expected api call is made for delete', async () => {
      await act(async () => {
        wrapper.find('DeleteButton').invoke('onConfirm')();
      });
      expect(HostsAPI.destroy).toHaveBeenCalledTimes(1);
    });

    test('Error dialog shown for failed deletion', async () => {
      HostsAPI.destroy.mockImplementationOnce(() =>
        Promise.reject(new Error())
      );
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

  describe('User has read-only permissions', () => {
    beforeAll(() => {
      const readOnlyHost = { ...mockHost };
      readOnlyHost.summary_fields.user_capabilities.edit = false;
      readOnlyHost.summary_fields.recent_jobs = [];

      wrapper = mountWithContexts(<HostDetail host={mockHost} />);
    });

    afterAll(() => {
      wrapper.unmount();
    });

    test('should hide activity stream when there are no recent jobs', async () => {
      expect(wrapper.find(`Detail[label="Activity"] Sparkline`)).toHaveLength(
        0
      );
    });

    test('should hide edit button for users without edit permission', async () => {
      expect(wrapper.find('Button[aria-label="edit"]').length).toBe(0);
    });
  });
});
