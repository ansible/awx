import React from 'react';
import { mount } from 'enzyme';
import CodeMirrorInput from './CodeMirrorInput';

describe('CodeMirrorInput', () => {
  beforeEach(() => {
    document.body.createTextRange = jest.fn();
  });

  it('should trigger onChange prop', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <CodeMirrorInput value="---\n" onChange={onChange} mode="yaml" />
    );
    const codemirror = wrapper.find('Controlled');
    expect(codemirror.prop('mode')).toEqual('yaml');
    expect(codemirror.prop('options').readOnly).toEqual(false);
    codemirror.prop('onBeforeChange')(null, null, 'newvalue');
    expect(onChange).toHaveBeenCalledWith('newvalue');
  });

  it('should render in read only mode', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <CodeMirrorInput value="---\n" onChange={onChange} mode="yaml" readOnly />
    );
    const codemirror = wrapper.find('Controlled');
    expect(codemirror.prop('options').readOnly).toEqual(true);
  });
});
