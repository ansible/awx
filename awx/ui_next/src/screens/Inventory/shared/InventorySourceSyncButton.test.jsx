import React from 'react';
import { act } from 'react-dom/test-utils';
import { InventorySourcesAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import InventorySourceSyncButton from './InventorySourceSyncButton';

jest.mock('../../../api');

const source = { id: 1, name: 'Foo', source: 'Source Bar' };
const onSyncLoading = jest.fn();

describe('<InventorySourceSyncButton />', () => {
  let wrapper;
  beforeEach(() => {
    wrapper = mountWithContexts(
      <InventorySourceSyncButton
        source={source}
        onSyncLoading={onSyncLoading}
        onFetchSources={() => {}}
      />
    );
  });
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should mount properly', () => {
    expect(wrapper.find('InventorySourceSyncButton').length).toBe(1);
  });

  test('should render start sync button', () => {
    expect(wrapper.find('SyncIcon').length).toBe(1);
    expect(
      wrapper.find('Button[aria-label="Start sync source"]').prop('isDisabled')
    ).toBe(false);
  });

  test('should start sync properly', async () => {
    InventorySourcesAPI.createSyncStart.mockResolvedValue({
      data: { status: 'pending' },
    });

    await act(async () =>
      wrapper.find('Button[aria-label="Start sync source"]').simulate('click')
    );
    expect(InventorySourcesAPI.createSyncStart).toBeCalledWith(1);
  });

  test('should throw error on sync start properly', async () => {
    InventorySourcesAPI.createSyncStart.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/inventory_sources/update',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Start sync source"]').simulate('click')
    );
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
  });
});
