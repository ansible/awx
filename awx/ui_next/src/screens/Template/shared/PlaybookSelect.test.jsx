import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import PlaybookSelect from './PlaybookSelect';
import { ProjectsAPI } from '../../../api';

jest.mock('../../../api');

describe('<PlaybookSelect />', () => {
  let wrapper;
  const onChange = jest.fn();
  beforeEach(async () => {
    ProjectsAPI.readPlaybooks.mockReturnValue({
      data: ['debug.yml', 'chatty.yml', 'tasks.yml'],
    });

    await act(async () => {
      wrapper = mountWithContexts(
        <PlaybookSelect
          projectId={1}
          isValid
          form={{}}
          field={{ value: '' }}
          helpers={{ setTouched: () => {} }}
          onError={() => {}}
          onChange={onChange}
        />
      );
    });
  });

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should reload playbooks when project value changes', async () => {
    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(1);
    await act(async () => {
      wrapper.setProps({ projectId: 15 });
    });

    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledTimes(2);
    expect(ProjectsAPI.readPlaybooks).toHaveBeenCalledWith(15);
  });

  test('should filter results properly', async () => {
    await act(async () => {
      wrapper.find('SelectToggle').prop('onToggle')();
    });
    wrapper.update();
    await act(async () => {
      wrapper
        .find('input[placeholder="Select a playbook"]')
        .simulate('change', {
          target: { value: 'chatty', name: 'playbook' },
        });
    });
    wrapper.update();

    expect(wrapper.find('SelectOption[value="chatty.yml"]').length).toBe(1);
  });

  test('should select playbook', async () => {
    act(() => wrapper.find('SelectToggle').prop('onToggle')());

    wrapper.update();
    act(() => {
      wrapper.find('Select').invoke('onSelect')({}, 'chatty.yml');
    });

    wrapper.update();
    expect(onChange).toBeCalledWith('chatty.yml');
  });

  test('should disable', async () => {
    ProjectsAPI.readPlaybooks.mockRejectedValue({
      response: { status: 403 },
    });
    let newWrapper;
    await act(async () => {
      newWrapper = mountWithContexts(
        <PlaybookSelect
          projectId={1}
          isValid
          form={{}}
          field={{ value: '' }}
          helpers={{ setTouched: () => {} }}
          onError={() => {}}
          onChange={onChange}
        />
      );
    });
    await waitForElement(
      newWrapper,
      'Select',
      el => el.prop('isDisabled') === true
    );
  });

  test('should show content error', async () => {
    ProjectsAPI.readPlaybooks.mockRejectedValue({
      response: { status: 400 },
    });

    const onError = jest.fn();
    await act(async () => {
      mountWithContexts(
        <PlaybookSelect
          projectId={1}
          isValid
          form={{}}
          field={{ value: '' }}
          helpers={{ setTouched: () => {} }}
          onError={onError}
          onChange={onChange}
        />
      );
    });
    expect(onError).toBeCalled();
  });
});
