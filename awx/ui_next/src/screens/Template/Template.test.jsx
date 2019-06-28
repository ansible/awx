import React from 'react';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import Template, { _Template } from './Template';

describe('<Template />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Template />);
  });
  test('When component mounts API is called and the response is put in state', async done => {
    const loadTemplate = jest.spyOn(_Template.prototype, 'loadTemplate');
    const wrapper = mountWithContexts(<Template />);
    await waitForElement(
      wrapper,
      'Template',
      el => el.state('hasContentLoading') === true
    );
    expect(loadTemplate).toHaveBeenCalled();
    await waitForElement(
      wrapper,
      'Template',
      el => el.state('hasContentLoading') === true
    );
    done();
  });
});
