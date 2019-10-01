import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import ContentLoading from './ContentLoading';

describe('ContentLoading', () => {
  test('renders the expected content', () => {
    const wrapper = mountWithContexts(<ContentLoading />);
    expect(wrapper).toHaveLength(1);
  });
});
