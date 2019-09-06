import React from 'react';
import { mount } from 'enzyme';
import JobStatusIcon from './JobStatusIcon';

describe('JobStatusIcon', () => {
  test('renders the successful job', () => {
    const wrapper = mount(<JobStatusIcon status="successful" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SuccessfulTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SuccessfulBottom')).toHaveLength(1);
  });
  test('renders running job', () => {
    const wrapper = mount(<JobStatusIcon status="running" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__RunningJob')).toHaveLength(1);
  });
  test('renders waiting job', () => {
    const wrapper = mount(<JobStatusIcon status="waiting" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__WaitingJob')).toHaveLength(1);
  });
  test('renders failed job', () => {
    const wrapper = mount(<JobStatusIcon status="failed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__FailedTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__FailedBottom')).toHaveLength(1);
  });
});
