import React from 'react';
import { act } from 'react-dom/test-utils';

import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';
import AssociateModal from './AssociateModal';
import mockHosts from './data.hosts.json';

jest.mock('../../api');

describe('<AssociateModal />', () => {
  let wrapper;
  const onClose = jest.fn();
  const onAssociate = jest.fn().mockResolvedValue();
  const fetchRequest = jest.fn().mockReturnValue({ data: { ...mockHosts } });
  const optionsRequest = jest.fn().mockResolvedValue({
    data: {
      actions: {
        GET: {},
        POST: {},
      },
      related_search_fields: [],
    },
  });

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <AssociateModal
          onClose={onClose}
          onAssociate={onAssociate}
          fetchRequest={fetchRequest}
          optionsRequest={optionsRequest}
          isModalOpen
        />
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render successfully', () => {
    expect(wrapper.find('AssociateModal').length).toBe(1);
  });

  test('should fetch and render list items', () => {
    expect(fetchRequest).toHaveBeenCalledTimes(1);
    expect(wrapper.find('CheckboxListItem').length).toBe(3);
  });

  test('should update selected list chips when items are selected', () => {
    expect(wrapper.find('SelectedList Chip')).toHaveLength(0);
    act(() => {
      wrapper
        .find('CheckboxListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.update();
    expect(wrapper.find('SelectedList Chip')).toHaveLength(1);
    wrapper.find('SelectedList Chip button').simulate('click');
    expect(wrapper.find('SelectedList Chip')).toHaveLength(0);
  });

  test('save button should call onAssociate', () => {
    act(() => {
      wrapper
        .find('CheckboxListItem')
        .first()
        .invoke('onSelect')();
    });
    wrapper.find('button[aria-label="Save"]').simulate('click');
    expect(onAssociate).toHaveBeenCalledTimes(1);
  });

  test('cancel button should call onClose', () => {
    wrapper.find('button[aria-label="Cancel"]').simulate('click');
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
