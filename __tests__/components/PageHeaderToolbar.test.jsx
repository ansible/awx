import React from 'react';
import { mount } from 'enzyme';

import { I18nProvider } from '@lingui/react';
import PageHeaderToolbar from '../../src/components/PageHeaderToolbar';

describe('PageHeaderToolbar', () => {
  test('renders the expected content', () => {
  const wrapper = mount(
    <I18nProvider>
      <PageHeaderToolbar />
    </I18nProvider>
  );
  expect(wrapper.find('Toolbar')).toHaveLength(1);
  });
});
