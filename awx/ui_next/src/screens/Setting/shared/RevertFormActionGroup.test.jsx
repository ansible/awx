import React from 'react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import RevertFormActionGroup from './RevertFormActionGroup';

describe('RevertFormActionGroup', () => {
  test('should render the expected content', () => {
    const wrapper = mountWithContexts(
      <RevertFormActionGroup
        onSubmit={() => {}}
        onCancel={() => {}}
        onRevert={() => {}}
      />
    );
    expect(wrapper).toHaveLength(1);
  });
});
