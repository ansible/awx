import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import AlertModal from './AlertModal';

describe('AlertModal', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <AlertModal title="Danger!">Are you sure?</AlertModal>
    );
    expect(wrapper).toHaveLength(1);
  });
});
