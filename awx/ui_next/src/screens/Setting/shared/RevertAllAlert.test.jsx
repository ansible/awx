import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import RevertAllAlert from './RevertAllAlert';

describe('RevertAllAlert', () => {
  test('renders the expected content', async () => {
    const wrapper = mountWithContexts(
      <RevertAllAlert onClose={() => {}} onRevertAll={() => {}} />
    );
    expect(wrapper).toHaveLength(1);
  });
});
