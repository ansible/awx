import React from 'react';
import { mount } from 'enzyme';
import HostStatusIcon from './HostStatusIcon';

describe('HostStatusIcon', () => {
  test('renders the "ok" host status', () => {
    const wrapper = mount(<HostStatusIcon status="ok" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SuccessfulTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SuccessfulBottom')).toHaveLength(1);
  });
  test('renders "failed" host status', () => {
    const wrapper = mount(<HostStatusIcon status="failed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__FailedTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__FailedBottom')).toHaveLength(1);
  });
  test('renders "changed" host status', () => {
    const wrapper = mount(<HostStatusIcon status="changed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__ChangedTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__ChangedBottom')).toHaveLength(1);
  });
  test('renders "skipped" host status', () => {
    const wrapper = mount(<HostStatusIcon status="skipped" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SkippedTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__SkippedBottom')).toHaveLength(1);
  });
  test('renders "unreachable" host status', () => {
    const wrapper = mount(<HostStatusIcon status="unreachable" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('StatusIcon__UnreachableTop')).toHaveLength(1);
    expect(wrapper.find('StatusIcon__UnreachableBottom')).toHaveLength(1);
  });
});
