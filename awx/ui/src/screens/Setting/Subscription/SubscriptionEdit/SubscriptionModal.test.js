import React from 'react';
import { act } from 'react-dom/test-utils';
import { ConfigAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import SubscriptionModal from './SubscriptionModal';

jest.mock('../../../../api');

describe('<SubscriptionModal />', () => {
  let wrapper;
  const onConfirm = jest.fn();
  const onClose = jest.fn();

  beforeAll(async () => {
    ConfigAPI.readSubscriptions = async () => ({
      data: [
        {
          subscription_name: 'mock A',
          instance_count: 100,
          license_date: 1714000271,
          pool_id: 7,
        },
        {
          subscription_name: 'mock B',
          instance_count: 200,
          license_date: 1714000271,
          pool_id: 8,
        },
        {
          subscription_name: 'mock C',
          instance_count: 30,
          license_date: 1714000271,
          pool_id: 9,
        },
      ],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SubscriptionModal
          subscriptionCreds={{
            username: 'admin',
            password: '$encrypted',
          }}
          onConfirm={onConfirm}
          onClose={onClose}
        />
      );
      await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    });
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('SubscriptionModal').length).toBe(1);
  });

  test('should render header', async () => {
    wrapper.update();
    const header = wrapper.find('tr').first().find('th');
    expect(header.at(0).text()).toEqual('');
    expect(header.at(1).text()).toEqual('Name');
    expect(header.at(2).text()).toEqual('Managed nodes');
    expect(header.at(3).text()).toEqual('Expires');
  });

  test('should render subscription rows', async () => {
    const rows = wrapper.find('tbody tr');
    expect(rows).toHaveLength(3);
    const firstRow = rows.at(0).find('td');
    expect(firstRow.at(0).find('input[type="radio"]')).toHaveLength(1);
    expect(firstRow.at(1).text()).toEqual('mock A');
    expect(firstRow.at(2).text()).toEqual('100');
    expect(firstRow.at(3).text()).toEqual('4/24/2024, 11:11:11 PM');
  });

  test('submit button should call onConfirm', async () => {
    expect(
      wrapper.find('Button[aria-label="Confirm selection"]').prop('isDisabled')
    ).toBe(true);
    await act(async () => {
      wrapper
        .find('SubscriptionModal SelectColumn')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();
    expect(
      wrapper.find('Button[aria-label="Confirm selection"]').prop('isDisabled')
    ).toBe(false);
    expect(onConfirm).toHaveBeenCalledTimes(0);
    expect(onClose).toHaveBeenCalledTimes(0);
    await act(async () =>
      wrapper.find('Button[aria-label="Confirm selection"]').prop('onClick')()
    );
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  test('should show empty content', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SubscriptionModal
          subscriptionCreds={{
            username: null,
            password: null,
          }}
        />
      );
      await waitForElement(wrapper, 'ContentEmpty', (el) => el.length === 1);
    });
  });

  test('should auto-select current selected subscription', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SubscriptionModal
          subscriptionCreds={{
            username: 'admin',
            password: '$encrypted',
          }}
          selectedSubscription={{
            id: 2,
          }}
        />
      );
      await waitForElement(wrapper, 'table');
      expect(wrapper.find('tr[id="row-1"] input').prop('checked')).toBe(false);
      expect(wrapper.find('tr[id="row-2"] input').prop('checked')).toBe(true);
      expect(wrapper.find('tr[id="row-3"] input').prop('checked')).toBe(false);
    });
  });

  test('should display error detail message', async () => {
    ConfigAPI.readSubscriptions = jest.fn();
    ConfigAPI.readSubscriptions.mockRejectedValueOnce(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SubscriptionModal
          subscriptionCreds={{
            username: 'admin',
            password: '$encrypted',
          }}
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    await waitForElement(wrapper, 'ErrorDetail', (el) => el.length === 1);
  });
});
