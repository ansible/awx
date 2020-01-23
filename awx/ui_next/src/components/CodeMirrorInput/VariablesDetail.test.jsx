import React from 'react';
import { act } from 'react-dom/test-utils';
import { shallow, mount } from 'enzyme';
import VariablesDetail from './VariablesDetail';

jest.mock('@api');

describe('<VariablesDetail>', () => {
  test('should render readonly CodeMirrorInput', () => {
    const wrapper = shallow(
      <VariablesDetail value="---foo: bar" label="Variables" />
    );
    const input = wrapper.find('Styled(CodeMirrorInput)');
    expect(input).toHaveLength(1);
    expect(input.prop('mode')).toEqual('yaml');
    expect(input.prop('value')).toEqual('---foo: bar');
    expect(input.prop('readOnly')).toEqual(true);
  });

  test('should detect JSON', () => {
    const wrapper = shallow(
      <VariablesDetail value='{"foo": "bar"}' label="Variables" />
    );
    const input = wrapper.find('Styled(CodeMirrorInput)');
    expect(input).toHaveLength(1);
    expect(input.prop('mode')).toEqual('javascript');
    expect(input.prop('value')).toEqual('{"foo": "bar"}');
  });

  test('should convert between modes', () => {
    const wrapper = shallow(
      <VariablesDetail value="---foo: bar" label="Variables" />
    );
    wrapper.find('YamlJsonToggle').invoke('onChange')('javascript');
    const input = wrapper.find('Styled(CodeMirrorInput)');
    expect(input.prop('mode')).toEqual('javascript');
    expect(input.prop('value')).toEqual('{\n  "foo": "bar"\n}');

    wrapper.find('YamlJsonToggle').invoke('onChange')('yaml');
    const input2 = wrapper.find('Styled(CodeMirrorInput)');
    expect(input2.prop('mode')).toEqual('yaml');
    expect(input2.prop('value')).toEqual('foo: bar\n');
  });

  test('should render label and value= --- when there are no values', () => {
    const wrapper = shallow(<VariablesDetail value="" label="Variables" />);
    expect(wrapper.find('Styled(CodeMirrorInput)').length).toBe(1);
    expect(wrapper.find('div.pf-c-form__label').text()).toBe('Variables');
  });

  test('should update value if prop changes', () => {
    const wrapper = mount(
      <VariablesDetail value="---foo: bar" label="Variables" />
    );
    act(() => {
      wrapper.find('YamlJsonToggle').invoke('onChange')('javascript');
    });
    wrapper.setProps({
      value: '---bar: baz',
    });
    wrapper.update();
    const input = wrapper.find('Styled(CodeMirrorInput)');
    expect(input.prop('mode')).toEqual('javascript');
    expect(input.prop('value')).toEqual('{\n  "bar": "baz"\n}');
  });
});
