import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import FormActionGroup from './FormActionGroup';

describe('FormActionGroup', () => {
  test('should render the expected content', () => {
    const wrapper = mountWithContexts(
      <FormActionGroup onSubmit={() => {}} onCancel={() => {}} />
    );
    expect(wrapper).toHaveLength(1);
  });
});
