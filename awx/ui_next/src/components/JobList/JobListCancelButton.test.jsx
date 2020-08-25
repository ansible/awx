import React from 'react';
import { shallow } from 'enzyme';
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
    const tooltipContents = wrapper.find('Tooltip').props().content;
    const renderedTooltipContents = shallow(tooltipContents);
    expect(
      renderedTooltipContents.matchesElement(
        <div>
          You do not have permission to cancel the following job: some job
        </div>
      )
    ).toBe(true);
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
    expect(wrapper.find('Tooltip').props().content).toBe('Cancel selected job');
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
    wrapper.find('AlertModal button[aria-label="Return"]').simulate('click');
    wrapper.update();
    expect(onCancel).toHaveBeenCalledTimes(0);
    expect(wrapper.find('AlertModal').length).toBe(0);
    expect(wrapper.find('AlertModal').length).toBe(0);
    wrapper.find('JobListCancelButton button').simulate('click');
    wrapper.update();
    expect(wrapper.find('AlertModal').length).toBe(1);
    wrapper
      .find('AlertModal button[aria-label="Cancel job"]')
      .simulate('click');
    wrapper.update();
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
