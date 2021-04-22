import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import AlertModal from './AlertModal';

describe('AlertModal', () => {
  test('renders the expected content', async () => {
    const wrapper = await act(async () => {
      mountWithContexts(<AlertModal title="Danger!">Are you sure?</AlertModal>);
    });
    expect(wrapper).toHaveLength(1);
  });
});
