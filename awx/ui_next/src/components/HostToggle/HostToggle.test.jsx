import React from 'react';
import { act } from 'react-dom/test-utils';
import { HostsAPI } from '../../api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import HostToggle from './HostToggle';

jest.mock('../../api');

const mockHost = {
  id: 1,
  name: 'Host 1',
  url: '/api/v2/hosts/1',
  inventory: 1,
  enabled: true,
  summary_fields: {
    inventory: {
      id: 1,
      name: 'inv 1',
    },
    user_capabilities: {
      delete: true,
      edit: true,
    },
    recent_jobs: [],
  },
};

describe('<HostToggle>', () => {
  test('should should toggle off', async () => {
    const onToggle = jest.fn();
    const wrapper = mountWithContexts(
      <HostToggle host={mockHost} onToggle={onToggle} />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(HostsAPI.update).toHaveBeenCalledWith(1, {
      enabled: false,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);
    expect(onToggle).toHaveBeenCalledWith(false);
  });

  test('should should toggle on', async () => {
    const onToggle = jest.fn();
    const wrapper = mountWithContexts(
      <HostToggle
        host={{
          ...mockHost,
          enabled: false,
        }}
        onToggle={onToggle}
      />
    );
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(false);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    expect(HostsAPI.update).toHaveBeenCalledWith(1, {
      enabled: true,
    });
    wrapper.update();
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);
    expect(onToggle).toHaveBeenCalledWith(true);
  });

  test('should be enabled', async () => {
    const wrapper = mountWithContexts(<HostToggle host={mockHost} />);
    expect(wrapper.find('Switch').prop('isDisabled')).toEqual(false);
  });

  test('should be disabled', async () => {
    const wrapper = mountWithContexts(
      <HostToggle isDisabled host={mockHost} />
    );
    expect(wrapper.find('Switch').prop('isDisabled')).toEqual(true);
  });

  test('should show error modal', async () => {
    HostsAPI.update.mockImplementation(() => {
      throw new Error('nope');
    });
    const wrapper = mountWithContexts(<HostToggle host={mockHost} />);
    expect(wrapper.find('Switch').prop('isChecked')).toEqual(true);

    await act(async () => {
      wrapper.find('Switch').invoke('onChange')();
    });
    wrapper.update();
    const modal = wrapper.find('AlertModal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('isOpen')).toEqual(true);

    act(() => {
      modal.invoke('onClose')();
    });
    wrapper.update();
    expect(wrapper.find('AlertModal')).toHaveLength(0);
  });
});
