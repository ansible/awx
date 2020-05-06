import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ContentEmpty from './ContentEmpty';

describe('ContentEmpty', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<ContentEmpty />);
    expect(wrapper).toHaveLength(1);
  });
});
