import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import { InventoriesAPI } from '../../../api';
import InventoryGroupsDeleteModal from './InventoryGroupsDeleteModal';

jest.mock('../../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
  }),
}));
describe('<InventoryGroupsDeleteModal />', () => {
  let wrapper;
  beforeEach(() => {
    act(() => {
      wrapper = mountWithContexts(
        <InventoryGroupsDeleteModal
          onAfterDelete={() => {}}
          isDisabled={false}
          groups={[
            { id: 1, name: 'Foo' },
            { id: 2, name: 'Bar' },
          ]}
        />
      );
    });
  });
  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });
  test('should mount properly', async () => {
    expect(wrapper.find('Button[aria-label="Delete"]').length).toBe(1);
    act(() => wrapper.find('Button[aria-label="Delete"]').prop('onClick')());
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
  });

  test('should close modal', () => {
    act(() => wrapper.find('Button[aria-label="Delete"]').prop('onClick')());
    wrapper.update();
    act(() => wrapper.find('ModalBoxCloseButton').prop('onClose')());
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(0);
  });

  test('should delete properly', async () => {
    act(() => wrapper.find('Button[aria-label="Delete"]').prop('onClick')({}));
    wrapper.update();
    act(() =>
      wrapper
        .find('Radio[label="Promote Child Groups and Hosts"]')
        .invoke('onChange')()
    );
    wrapper.update();
    expect(
      wrapper.find('Button[aria-label="Confirm Delete"]').prop('isDisabled')
    ).toBe(false);
    await act(() =>
      wrapper.find('Button[aria-label="Confirm Delete"]').prop('onClick')()
    );
    expect(InventoriesAPI.promoteGroup).toBeCalledWith(1, 1);
  });

  test('should throw deletion error ', async () => {
    InventoriesAPI.promoteGroup.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/v2/inventories/1/groups',
          },
          data: 'An error occurred',
          status: 403,
        },
      })
    );
    act(() => wrapper.find('Button[aria-label="Delete"]').prop('onClick')({}));
    wrapper.update();
    act(() =>
      wrapper
        .find('Radio[label="Promote Child Groups and Hosts"]')
        .invoke('onChange')()
    );
    wrapper.update();
    expect(
      wrapper.find('Button[aria-label="Confirm Delete"]').prop('isDisabled')
    ).toBe(false);
    await act(() =>
      wrapper.find('Button[aria-label="Confirm Delete"]').prop('onClick')()
    );
    expect(InventoriesAPI.promoteGroup).toBeCalledWith(1, 1);
    wrapper.update();
    expect(wrapper.find('ErrorDetail').length).toBe(1);
  });
});
