import React from 'react';
import { mount } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import JobStatusIcon from './JobStatusIcon';

describe('JobStatusIcon', () => {
  const job = {
    id: 1,
    status: 'successful'
  };

  test('renders the expected content', () => {
    const wrapper = mount(<JobStatusIcon job={job} />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('Tooltip')).toHaveLength(0);
    expect(wrapper.find('Link')).toHaveLength(0);
  });
  test('renders with tooltip if tooltip passed', () => {
    const wrapper = mount(<JobStatusIcon job={job} tooltip="Foo Bar" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('Tooltip')).toHaveLength(1);
    expect(wrapper.find('Link')).toHaveLength(0);
  });
  test('renders with link if link passed', () => {
    const wrapper = mountWithContexts(<JobStatusIcon job={job} link="/jobs/playbook/1" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('Tooltip')).toHaveLength(0);
    expect(wrapper.find('Link')).toHaveLength(1);
  });
  test('renders running job', () => {
    const runningJob = {
      id: 2,
      status: 'running'
    };
    const wrapper = mount(<JobStatusIcon job={runningJob} />);
    expect(wrapper.find('JobStatusIcon__RunningJob')).toHaveLength(1);
  });
  test('renders waiting job', () => {
    const waitingJob = {
      id: 3,
      status: 'waiting'
    };
    const wrapper = mount(<JobStatusIcon job={waitingJob} />);
    expect(wrapper.find('JobStatusIcon__WaitingJob')).toHaveLength(1);
  });
  test('renders failed job', () => {
    const failedJob = {
      id: 4,
      status: 'failed'
    };
    const wrapper = mount(<JobStatusIcon job={failedJob} />);
    expect(wrapper.find('JobStatusIcon__FailedTop')).toHaveLength(1);
    expect(wrapper.find('JobStatusIcon__FailedBottom')).toHaveLength(1);
  });
  test('renders successful job', () => {
    const wrapper = mount(<JobStatusIcon job={job} />);
    expect(wrapper.find('JobStatusIcon__SuccessfulTop')).toHaveLength(1);
    expect(wrapper.find('JobStatusIcon__SuccessfulBottom')).toHaveLength(1);
  });
});