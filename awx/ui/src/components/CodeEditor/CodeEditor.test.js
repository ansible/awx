import React from 'react';
import debounce from 'util/debounce';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import CodeEditor from './CodeEditor';

jest.mock('../../util/debounce');

describe('CodeEditor', () => {
  beforeEach(() => {
    document.body.createTextRange = jest.fn();
  });

  it('should pass value and mode through to ace editor', () => {
    const onChange = jest.fn();
    const wrapper = mountWithContexts(
      <CodeEditor value={'---\nfoo: bar'} onChange={onChange} mode="yaml" />
    );
    const aceEditor = wrapper.find('AceEditor');
    expect(aceEditor.prop('mode')).toEqual('yaml');
    expect(aceEditor.prop('setOptions').readOnly).toEqual(false);
    expect(aceEditor.prop('value')).toEqual('---\nfoo: bar');
  });

  it('should trigger onChange prop', () => {
    debounce.mockImplementation((fn) => fn);
    const onChange = jest.fn();
    const wrapper = mountWithContexts(
      <CodeEditor value="---" onChange={onChange} mode="yaml" />
    );
    const aceEditor = wrapper.find('AceEditor');
    aceEditor.prop('onChange')('newvalue');
    expect(onChange).toHaveBeenCalledWith('newvalue');
  });

  it('should render in read only mode', () => {
    const onChange = jest.fn();
    const wrapper = mountWithContexts(
      <CodeEditor value="---" onChange={onChange} mode="yaml" readOnly />
    );
    const aceEditor = wrapper.find('AceEditor');
    expect(aceEditor.prop('setOptions').readOnly).toEqual(true);
    expect(aceEditor.prop('value')).toEqual('---');
  });
});
