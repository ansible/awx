import React from 'react';
import { mount } from 'enzyme';
import CodeEditor from './CodeEditor';

describe('CodeEditor', () => {
  beforeEach(() => {
    document.body.createTextRange = jest.fn();
  });

  it('should trigger onChange prop', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <CodeEditor value="---" onChange={onChange} mode="yaml" />
    );
    const aceEditor = wrapper.find('AceEditor');
    expect(aceEditor.prop('mode')).toEqual('yaml');
    expect(aceEditor.prop('setOptions').readOnly).toEqual(false);
    expect(aceEditor.prop('value')).toEqual('---');
    aceEditor.prop('onChange')('newvalue');
    expect(onChange).toHaveBeenCalledWith('newvalue');
  });

  it('should render in read only mode', () => {
    const onChange = jest.fn();
    const wrapper = mount(
      <CodeEditor value="---" onChange={onChange} mode="yaml" readOnly />
    );
    const aceEditor = wrapper.find('AceEditor');
    expect(aceEditor.prop('setOptions').readOnly).toEqual(true);
    expect(aceEditor.prop('value')).toEqual('---');
  });
});
