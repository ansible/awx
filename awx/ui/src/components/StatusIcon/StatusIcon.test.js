import React from 'react';
import { mount } from 'enzyme';
import StatusIcon from './StatusIcon';

describe('StatusIcon', () => {
  test('renders the successful status', () => {
    const wrapper = mount(<StatusIcon status="successful" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('CheckCircleIcon')).toHaveLength(1);
  });

  test('renders running status', () => {
    const wrapper = mount(<StatusIcon status="running" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('RunningIcon')).toHaveLength(1);
  });

  test('renders waiting status', () => {
    const wrapper = mount(<StatusIcon status="waiting" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ClockIcon')).toHaveLength(1);
  });

  test('renders failed status', () => {
    const wrapper = mount(<StatusIcon status="failed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationCircleIcon')).toHaveLength(1);
  });

  test('renders a successful status when host status is "ok"', () => {
    const wrapper = mount(<StatusIcon status="ok" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('CheckCircleIcon')).toHaveLength(1);
  });

  test('renders "failed" host status', () => {
    const wrapper = mount(<StatusIcon status="failed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationCircleIcon')).toHaveLength(1);
  });

  test('renders "changed" host status', () => {
    const wrapper = mount(<StatusIcon status="changed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationTriangleIcon')).toHaveLength(1);
  });

  test('renders "skipped" host status', () => {
    const wrapper = mount(<StatusIcon status="skipped" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('MinusCircleIcon')).toHaveLength(1);
  });

  test('renders "unreachable" host status', () => {
    const wrapper = mount(<StatusIcon status="unreachable" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationCircleIcon')).toHaveLength(1);
  });
});
