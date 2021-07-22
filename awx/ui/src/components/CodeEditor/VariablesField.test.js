import React from 'react';
import { act } from 'react-dom/test-utils';
import { Formik } from 'formik';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import VariablesField from './VariablesField';

describe('VariablesField', () => {
  it('should render code editor', () => {
    const value = '---\n';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const codeEditor = wrapper.find('CodeEditor');
    expect(codeEditor.prop('value')).toEqual(value);
  });

  it('should toggle between yaml/json', async () => {
    const value = '---\nfoo: bar\nbaz: 3';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const buttons = wrapper.find('Button');
    expect(buttons).toHaveLength(3);
    expect(buttons.at(0).prop('variant')).toEqual('primary');
    expect(buttons.at(1).prop('variant')).toEqual('secondary');
    await act(async () => {
      buttons.at(1).simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('javascript');
    expect(wrapper.find('CodeEditor').prop('value')).toEqual(
      '{\n  "foo": "bar",\n  "baz": 3\n}'
    );
    const buttons2 = wrapper.find('Button');
    expect(buttons2.at(0).prop('variant')).toEqual('secondary');
    expect(buttons2.at(1).prop('variant')).toEqual('primary');
    await act(async () => {
      buttons2.at(0).simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('yaml');
    expect(wrapper.find('CodeEditor').prop('value')).toEqual(
      '---\nfoo: bar\nbaz: 3'
    );
  });

  it('should retain non-expanded yaml if JSON value not edited', async () => {
    const value = '---\na: &aa [a,b,c]\nb: *aa';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const jsButton = wrapper.find('Button.toggle-button-javascript');
    await act(async () => {
      jsButton.simulate('click');
    });
    wrapper.update();
    const yamlButton = wrapper.find('Button.toggle-button-yaml');
    await act(async () => {
      yamlButton.simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('yaml');
    expect(wrapper.find('CodeEditor').prop('value')).toEqual(value);
  });

  it('should retain expanded yaml if JSON value is edited', async () => {
    const value = '---\na: &aa [a,b,c]\nb: *aa';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    const jsButton = wrapper.find('Button.toggle-button-javascript');
    await act(async () => {
      jsButton.simulate('click');
    });
    wrapper.update();
    wrapper.find('CodeEditor').invoke('onChange')(
      '{\n  "foo": "bar",\n  "baz": 3\n}'
    );
    const yamlButton = wrapper.find('Button.toggle-button-yaml');
    await act(async () => {
      yamlButton.simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('yaml');
    expect(wrapper.find('CodeEditor').prop('value')).toEqual(
      'foo: bar\nbaz: 3\n'
    );
  });

  it('should retain non-expanded yaml if YAML value is edited', async () => {
    const value = '---\na: &aa [a,b,c]\nb: *aa';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }}>
        {() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      </Formik>
    );
    wrapper.find('CodeEditor').invoke('onChange')(
      '---\na: &aa [a,b,c]\nb: *aa\n'
    );
    const buttons = wrapper.find('Button');
    await act(async () => {
      buttons.at(1).simulate('click');
    });
    wrapper.update();
    const buttons2 = wrapper.find('Button');
    await act(async () => {
      buttons2.at(0).simulate('click');
    });
    wrapper.update();
    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('yaml');
    expect(wrapper.find('CodeEditor').prop('value')).toEqual(
      '---\na: &aa [a,b,c]\nb: *aa\n'
    );
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
    wrapper.find('Button').at(1).simulate('click');
    wrapper.update();

    const field = wrapper.find('CodeEditor');
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
    expect(wrapper.find('Popover[data-cy="the-field-tooltip"]').length).toBe(1);
  });

  it('should submit value through Formik', async () => {
    const value = '---\nfoo: bar\n';
    const handleSubmit = jest.fn();
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }} onSubmit={handleSubmit}>
        {(formik) => (
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
      wrapper.find('CodeEditor').invoke('onChange')('---\nnewval: changed');
      wrapper.find('form').simulate('submit');
    });

    expect(handleSubmit).toHaveBeenCalled();
    expect(handleSubmit.mock.calls[0][0]).toEqual({
      variables: '---\nnewval: changed',
    });
  });

  it('should initialize to JSON if value is JSON', async () => {
    const value = '{"foo": "bar"}';
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ variables: value }} onSubmit={jest.fn()}>
          {(formik) => (
            <form onSubmit={formik.handleSubmit}>
              <VariablesField
                id="the-field"
                name="variables"
                label="Variables"
              />
              <button type="submit" id="submit">
                Submit
              </button>
            </form>
          )}
        </Formik>
      );
    });
    wrapper.update();

    expect(wrapper.find('CodeEditor').prop('mode')).toEqual('javascript');
  });

  it('should open modal when expanded', async () => {
    const value = '---';
    const wrapper = mountWithContexts(
      <Formik initialValues={{ variables: value }} onSubmit={jest.fn()}>
        {(formik) => (
          <form onSubmit={formik.handleSubmit}>
            <VariablesField id="the-field" name="variables" label="Variables" />
            <button type="submit" id="submit">
              Submit
            </button>
          </form>
        )}
      </Formik>
    );
    expect(wrapper.find('Modal').prop('isOpen')).toEqual(false);

    wrapper.find('Button[variant="plain"]').invoke('onClick')();
    wrapper.update();

    expect(wrapper.find('Modal').prop('isOpen')).toEqual(true);
    expect(wrapper.find('Modal CodeEditor')).toHaveLength(1);
  });

  it('should format JSON for code editor', async () => {
    const value = '{"foo": "bar"}';
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Formik initialValues={{ variables: value }} onSubmit={jest.fn()}>
          {(formik) => (
            <form onSubmit={formik.handleSubmit}>
              <VariablesField
                id="the-field"
                name="variables"
                label="Variables"
              />
              <button type="submit" id="submit">
                Submit
              </button>
            </form>
          )}
        </Formik>
      );
    });
    wrapper.update();

    expect(wrapper.find('CodeEditor').prop('value')).toEqual(
      '{\n  "foo": "bar"\n}'
    );
  });
});
