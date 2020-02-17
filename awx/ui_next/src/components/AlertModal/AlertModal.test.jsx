import React from 'react';
import { mount } from 'enzyme';

import AlertModal from './AlertModal';

describe('AlertModal', () => {
  test('renders the expected content', () => {
    const wrapper = mount(
      <AlertModal title="Danger!">Are you sure?</AlertModal>
    );
    expect(wrapper).toHaveLength(1);
  });
});
