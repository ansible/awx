import React from 'react';
import { mount } from 'enzyme';
import { Formik } from 'formik';
import { sleep } from '../../../testUtils/testUtils';
import VariablesField from './VariablesField';

describe('VariablesField', () => {
  beforeEach(() => {
    document.body.createTextRange = jest.fn();
  });

  it('should render code mirror input', () => {
    const value = '---\n';
    const wrapper = mount(
      <Formik
        initialValues={{ variables: value }}
        render={() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      />
    );
    const codemirror = wrapper.find('Controlled');
    expect(codemirror.prop('value')).toEqual(value);
  });

  it('should render yaml/json toggles', () => {
    const value = '---\n';
    const wrapper = mount(
      <Formik
        initialValues={{ variables: value }}
        render={() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      />
    );
    const buttons = wrapper.find('Button');
    expect(buttons).toHaveLength(2);
    expect(buttons.at(0).prop('variant')).toEqual('primary');
    expect(buttons.at(1).prop('variant')).toEqual('secondary');

    buttons.at(1).simulate('click');
    wrapper.update(0);
    expect(wrapper.find('CodeMirrorInput').prop('mode')).toEqual('javascript');
    const buttons2 = wrapper.find('Button');
    expect(buttons2.at(0).prop('variant')).toEqual('secondary');
    expect(buttons2.at(1).prop('variant')).toEqual('primary');
    buttons2.at(0).simulate('click');
    wrapper.update(0);
    expect(wrapper.find('CodeMirrorInput').prop('mode')).toEqual('yaml');
  });

  it('should set Formik error if yaml is invalid', () => {
    const value = '---\nfoo bar\n';
    const wrapper = mount(
      <Formik
        initialValues={{ variables: value }}
        render={() => (
          <VariablesField id="the-field" name="variables" label="Variables" />
        )}
      />
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

  it('should submit value through Formik', async () => {
    const value = '---\nfoo: bar\n';
    const handleSubmit = jest.fn();
    const wrapper = mount(
      <Formik
        initialValues={{ variables: value }}
        onSubmit={handleSubmit}
        render={formik => (
          <form onSubmit={formik.handleSubmit}>
            <VariablesField id="the-field" name="variables" label="Variables" />
            <button type="submit" id="submit">
              Submit
            </button>
          </form>
        )}
      />
    );
    wrapper.find('CodeMirrorInput').prop('onChange')('---\nnewval: changed');
    wrapper.find('form').simulate('submit');
    await sleep(1);
    await sleep(1);

    expect(handleSubmit).toHaveBeenCalled();
    expect(handleSubmit.mock.calls[0][0]).toEqual({
      variables: '---\nnewval: changed',
    });
  });
});
