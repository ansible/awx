import React from 'react';
import { mount } from 'enzyme';
import StatusLabel from './StatusLabel';

describe('StatusLabel', () => {
  test('should render success', () => {
    const wrapper = mount(<StatusLabel status="success" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('CheckCircleIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('green');
    expect(wrapper.text()).toEqual('Success');
  });

  test('should render failed', () => {
    const wrapper = mount(<StatusLabel status="failed" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationCircleIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('red');
    expect(wrapper.text()).toEqual('Failed');
  });

  test('should render error', () => {
    const wrapper = mount(<StatusLabel status="error" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationCircleIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('red');
    expect(wrapper.text()).toEqual('Error');
  });

  test('should render running', () => {
    const wrapper = mount(<StatusLabel status="running" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('SyncAltIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('blue');
    expect(wrapper.text()).toEqual('Running');
  });

  test('should render pending', () => {
    const wrapper = mount(<StatusLabel status="pending" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ClockIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('blue');
    expect(wrapper.text()).toEqual('Pending');
  });

  test('should render waiting', () => {
    const wrapper = mount(<StatusLabel status="waiting" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ClockIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('grey');
    expect(wrapper.text()).toEqual('Waiting');
  });

  test('should render canceled', () => {
    const wrapper = mount(<StatusLabel status="canceled" />);
    expect(wrapper).toHaveLength(1);
    expect(wrapper.find('ExclamationTriangleIcon')).toHaveLength(1);
    expect(wrapper.find('Label').prop('color')).toEqual('orange');
    expect(wrapper.text()).toEqual('Canceled');
  });
});
