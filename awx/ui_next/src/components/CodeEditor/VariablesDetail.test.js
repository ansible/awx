import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import VariablesDetail from './VariablesDetail';

jest.mock('../../api');

describe('<VariablesDetail>', () => {
  test('should render readonly CodeEditor', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="---foo: bar" label="Variables" name="test" />
    );
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input).toHaveLength(1);
    expect(input.prop('mode')).toEqual('yaml');
    expect(input.prop('value')).toEqual('---foo: bar');
    expect(input.prop('readOnly')).toEqual(true);
  });

  test('should detect JSON', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value='{"foo": "bar"}' label="Variables" name="test" />
    );
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input).toHaveLength(1);
    expect(input.prop('mode')).toEqual('javascript');
  });

  test('should format JSON', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value='{"foo": "bar"}' label="Variables" name="test" />
    );
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input).toHaveLength(1);
    expect(input.prop('value')).toEqual('{\n  "foo": "bar"\n}');
  });

  test('should convert between modes', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="---foo: bar" label="Variables" name="test" />
    );
    wrapper.find('MultiButtonToggle').invoke('onChange')('javascript');
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input.prop('mode')).toEqual('javascript');
    expect(input.prop('value')).toEqual('{\n  "foo": "bar"\n}');

    wrapper.find('MultiButtonToggle').invoke('onChange')('yaml');
    const input2 = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input2.prop('mode')).toEqual('yaml');
    expect(input2.prop('value')).toEqual('---foo: bar');
  });

  test('should render label and value --- when there are no values', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="" label="Variables" name="test" />
    );
    expect(wrapper.find('VariablesDetail___StyledCodeEditor').length).toBe(1);
    expect(wrapper.find('.pf-c-form__label').text()).toBe('Variables');
  });

  test('should update value if prop changes', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="---foo: bar" label="Variables" name="test" />
    );
    act(() => {
      wrapper.find('MultiButtonToggle').invoke('onChange')('javascript');
    });
    wrapper.setProps({
      value: '---bar: baz',
    });
    wrapper.update();
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input.prop('mode')).toEqual('javascript');
    expect(input.prop('value')).toEqual('{\n  "bar": "baz"\n}');
  });

  test('should default yaml value to "---"', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="" label="Variables" name="test" />
    );
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input.prop('value')).toEqual('---');
  });

  test('should default empty json to "{}"', () => {
    const wrapper = mountWithContexts(
      <VariablesDetail value="" label="Variables" name="test" />
    );
    act(() => {
      wrapper.find('MultiButtonToggle').invoke('onChange')('javascript');
    });
    wrapper.setProps({ value: '' });
    const input = wrapper.find('VariablesDetail___StyledCodeEditor');
    expect(input.prop('value')).toEqual('{}');
  });
});
