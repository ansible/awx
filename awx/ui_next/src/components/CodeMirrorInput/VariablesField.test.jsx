import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import VariablesField from './VariablesField';

describe('VariablesField', () => {
  beforeEach(() => {
    document.body.createTextRange = jest.fn();
  });

  it('should render code mirror input', () => {
    const value = '---\n';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const codemirror = wrapper.find('Controlled');
    expect(codemirror.prop('value')).toEqual(value);
  });

  it('should render yaml/json toggles', async () => {
    const value = '---\n';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const buttons = wrapper.find('Button');
    expect(buttons).toHaveLength(2);
    expect(buttons.at(0).prop('variant')).toEqual('primary');
    expect(buttons.at(1).prop('variant')).toEqual('secondary');
    await act(async () => {
      buttons.at(1).simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeMirrorInput').prop('mode')).toEqual('javascript');
    const buttons2 = wrapper.find('Button');
    expect(buttons2.at(0).prop('variant')).toEqual('secondary');
    expect(buttons2.at(1).prop('variant')).toEqual('primary');
    await act(async () => {
      buttons2.at(0).simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeMirrorInput').prop('mode')).toEqual('yaml');
  });

  it('should set Formik error if yaml is invalid', async () => {
    const value = '---\nfoo bar\n';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    wrapper
      .find('Button')
      .at(1)
      .simulate('click');
    wrapper.update();

    const field = wrapper.find('CodeMirrorInput');
    expect(field.prop('hasErrors')).toEqual(true);
    expect(wrapper.find('.pf-m-error')).toHaveLength(1);
  });
  it('should render tooltip', () => {
    const value = '---\n';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField
            id="the-field"
            name="variables"
            label="Variables"
            tooltip="This is a tooltip"
          />
        )}
      </Formik>
    );
    expect(wrapper.find('Popover[data-cy="the-field"]').length).toBe(1);
  });

  it('should submit value through Formik', async () => {
    const value = '---\nfoo: bar\n';
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }} onSubmit={handleSubmit}>
        {formik => (
          <form onSubmit={formik.handleSubmit}>
            <VariablesField id="the-field" name="variables" label="Variables" />
            <button type="submit" id="submit">
              Submit
            </button>
          </form>
        )}
      </Formik>
    );
    await act(async () => {
      wrapper.find('CodeMirrorInput').invoke('onChange')(
        '---\nnewval: changed'
      );
      wrapper.find('form').simulate('submit');
    });

    expect(handleSubmit).toHaveBeenCalled();
    expect(handleSubmit.mock.calls[0][0]).toEqual({
      variables: '---\nnewval: changed',
    });
  });

  it('should initialize to JSON if value is JSON', async () => {
    const value = '{"foo": "bar"}';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }} onSubmit={jest.fn()}>
        {formik => (
          <form onSubmit={formik.handleSubmit}>
            <VariablesField id="the-field" name="variables" label="Variables" />
            <button type="submit" id="submit">
              Submit
            </button>
          </form>
        )}
      </Formik>
    );

    expect(wrapper.find('CodeMirrorInput').prop('mode')).toEqual('javascript');
  });
});
