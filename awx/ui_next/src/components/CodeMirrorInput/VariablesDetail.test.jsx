import React from 'react';
import { shallow } from 'enzyme';
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
});
