import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import JobListCancelButton from './JobListCancelButton';

describe('<JobListCancelButton />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
  });
  test('should be disabled when no rows are selected', () => {
    wrapper = mountWithContexts(<JobListCancelButton jobsToCancel={[]} />);
    expect(wrapper.find('JobListCancelButton button').props().disabled).toBe(
      true
    );
    expect(wrapper.find('Tooltip').props().content).toBe(
      'Select a job to cancel'
    );
  });
  test('should be disabled when user does not have permissions to cancel selected job', () => {
    wrapper = mountWithContexts(
      <JobListCancelButton
        jobsToCancel={[
          {
            id: 1,
            name: 'some job',
            summary_fields: {
              user_capabilities: {
                delete: false,
                start: false,
              },
            },
          },
        ]}
      />
    );
    expect(wrapper.find('JobListCancelButton button').props().disabled).toBe(
      true
    );
  });
  test('should be enabled when user does have permission to cancel selected job', () => {
    wrapper = mountWithContexts(
      <JobListCancelButton
        jobsToCancel={[
          {
            id: 1,
            name: 'some job',
            summary_fields: {
              user_capabilities: {
                delete: true,
                start: true,
              },
            },
          },
        ]}
      />
    );
    expect(wrapper.find('JobListCancelButton button').props().disabled).toBe(
      false
    );
  });
  test('modal functions as expected', () => {
    const onCancel = jest.fn();
    wrapper = mountWithContexts(
      <JobListCancelButton
        jobsToCancel={[
          {
            id: 1,
            name: 'some job',
            summary_fields: {
              user_capabilities: {
                delete: true,
                start: true,
              },
            },
          },
        ]}
        onCancel={onCancel}
      />
    );
    expect(wrapper.find('AlertModal').length).toBe(0);
    wrapper.find('JobListCancelButton button').simulate('click');
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    wrapper.find('button#cancel-job-return-button').simulate('click');
    wrapper.update();
    expect(onCancel).toHaveBeenCalledTimes(0);
    expect(wrapper.find('AlertModal').length).toBe(0);
    expect(wrapper.find('AlertModal').length).toBe(0);
    wrapper.find('JobListCancelButton button').simulate('click');
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    wrapper.find('button#cancel-job-confirm-button').simulate('click');
    wrapper.update();
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
