import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';

import FormActionGroup from './FormActionGroup';

describe('FormActionGroup', () => {
  test('should render the expected content', () => {
    const wrapper = mountWithContexts(
      <FormActionGroup onSubmit={() => {}} onCancel={() => {}} />
    );
    expect(wrapper).toHaveLength(1);
  });

  test('should display error message if given', () => {
    const wrapper = mountWithContexts(
      <FormActionGroup
        onSubmit={() => {}}
        onCancel={() => {}}
        errorMessage={<div className="error">oh noes</div>}
      />
    );
    expect(wrapper.find('.error').text()).toEqual('oh noes');
  });
});
