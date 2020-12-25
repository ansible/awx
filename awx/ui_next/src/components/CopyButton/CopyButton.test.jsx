import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import CopyButton from './CopyButton';

jest.mock('../../api');

describe('<CopyButton/>', () => {
  test('shold mount properly', () => {
    const wrapper = mountWithContexts(
      <CopyButton
        onCopyStart={() => {}}
        onCopyFinish={() => {}}
        copyItem={() => {}}
        helperText={{
          tooltip: `Copy Template`,
          errorMessage: `Failed to copy template.`,
        }}
      />
    );
    expect(wrapper.find('CopyButton').length).toBe(1);
  });
  test('should render proper tooltip', () => {
    const wrapper = mountWithContexts(
      <CopyButton
        onCopyStart={() => {}}
        onCopyFinish={() => {}}
        copyItem={() => {}}
        helperText={{
          tooltip: `Copy Template`,
          errorMessage: `Failed to copy template.`,
        }}
      />
    );
    expect(wrapper.find('Tooltip').prop('content')).toBe('Copy Template');
  });
});
