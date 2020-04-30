import React from 'react';
import { InventoryUpdatesAPI, InventorySourcesAPI } from '@api';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import InventorySourceSyncButton from './InventorySourceSyncButton';

jest.mock('@api/models/InventoryUpdates');
jest.mock('@api/models/InventorySources');

const source = { id: 1, name: 'Foo', source: 'Source Bar' };
const onCancelSyncLoading = jest.fn();
const onStartSyncLoading = jest.fn();

describe('<InventorySourceSyncButton />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(
      <InventorySourceSyncButton
        source={source}
        onCancelSyncLoading={onCancelSyncLoading}
        onStartSyncLoading={onStartSyncLoading}
      />
    );
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('should mount properly', async () => {
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
  });

  test('should render start sync button', async () => {
    expect(wrapper.find('SyncIcon').length).toBe(1);
    expect(
      wrapper.find('Button[aria-label="Start sync source"]').prop('isDisabled')
    ).toBe(false);
  });

  test('should render cancel sync button', async () => {
    wrapper = mountWithContexts(
      <InventorySourceSyncButton
        source={{ status: 'pending', ...source }}
        onCancelSyncLoading={onCancelSyncLoading}
        onStartSyncLoading={onStartSyncLoading}
      />
    );
    expect(wrapper.find('MinusCircleIcon').length).toBe(1);
  });

  test('should start sync properly', async () => {
    InventorySourcesAPI.allowSyncStart.mockResolvedValue({
      data: { can_update: true },
    });
    InventorySourcesAPI.startSyncSource.mockResolvedValue({
      data: { status: 'pending' },
    });

    await act(async () =>
      wrapper.find('Button[aria-label="Start sync source"]').simulate('click')
    );
    expect(InventorySourcesAPI.allowSyncStart).toBeCalledWith(1);
    expect(InventorySourcesAPI.startSyncSource).toBeCalledWith(1);
    wrapper.update();
    expect(wrapper.find('Button[aria-label="Cancel sync source"]').length).toBe(
      1
    );
  });
  test('should cancel sync properly', async () => {
    InventorySourcesAPI.readDetail.mockResolvedValue({
      data: { summary_fields: { current_update: { id: 120 } } },
    });
    InventoryUpdatesAPI.allowSyncCancel.mockResolvedValue({
      data: { can_cancel: true },
    });
    InventoryUpdatesAPI.cancelSyncSource.mockResolvedValue({
      data: { status: '' },
    });

    wrapper = mountWithContexts(
      <InventorySourceSyncButton
        source={{ status: 'pending', ...source }}
        onCancelSyncLoading={onCancelSyncLoading}
        onStartSyncLoading={onStartSyncLoading}
      />
    );
    expect(wrapper.find('Button[aria-label="Cancel sync source"]').length).toBe(
      1
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Cancel sync source"]').simulate('click')
    );

    expect(InventorySourcesAPI.readDetail).toBeCalledWith(1);
    expect(InventoryUpdatesAPI.allowSyncCancel).toBeCalledWith(120);
    expect(InventoryUpdatesAPI.cancelSyncSource).toBeCalledWith(120);

    wrapper.update();

    expect(wrapper.find('Button[aria-label="Start sync source"]').length).toBe(
      1
    );
  });
  test('Should prevent user from starting sync', async () => {
    InventorySourcesAPI.allowSyncStart.mockResolvedValue({
      data: { can_update: false },
    });
    InventorySourcesAPI.startSyncSource.mockResolvedValue({
      data: { status: 'pending' },
    });

    await act(async () =>
      wrapper.find('Button[aria-label="Start sync source"]').simulate('click')
    );
    expect(InventorySourcesAPI.allowSyncStart).toBeCalledWith(1);
    expect(InventorySourcesAPI.startSyncSource).not.toBeCalledWith();
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    expect(wrapper.find('Button[aria-label="Start sync source"]').length).toBe(
      1
    );
  });
  test('should prevent user from canceling sync', async () => {
    InventorySourcesAPI.readDetail.mockResolvedValue({
      data: { summary_fields: { current_update: { id: 120 } } },
    });
    InventoryUpdatesAPI.allowSyncCancel.mockResolvedValue({
      data: { can_cancel: false },
    });
    InventoryUpdatesAPI.cancelSyncSource.mockResolvedValue({
      data: { status: '' },
    });

    wrapper = mountWithContexts(
      <InventorySourceSyncButton
        source={{ status: 'pending', ...source }}
        onCancelSyncLoading={onCancelSyncLoading}
        onStartSyncLoading={onStartSyncLoading}
      />
    );
    expect(wrapper.find('Button[aria-label="Cancel sync source"]').length).toBe(
      1
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Cancel sync source"]').simulate('click')
    );

    expect(InventorySourcesAPI.readDetail).toBeCalledWith(1);
    expect(InventoryUpdatesAPI.allowSyncCancel).toBeCalledWith(120);
    expect(InventoryUpdatesAPI.cancelSyncSource).not.toBeCalledWith(120);

    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    expect(wrapper.find('Button[aria-label="Cancel sync source"]').length).toBe(
      1
    );
  });
});
