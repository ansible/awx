import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import CopyButton from './CopyButton';

jest.mock('../../api');

let wrapper;

describe('<CopyButton/>', () => {
  test('should mount properly', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <CopyButton
          onCopyStart={() => {}}
          onCopyFinish={() => {}}
          copyItem={() => {}}
          errorMessage="Failed to copy template."
        />
      );
    });
    expect(wrapper.find('CopyButton').length).toBe(1);
  });

  test('should call the correct function on button click', async () => {
    const copyItem = jest.fn();
    await act(async () => {
      wrapper = mountWithContexts(
        <CopyButton
          onCopyStart={() => {}}
          onCopyFinish={() => {}}
          copyItem={copyItem}
          errorMessage="Failed to copy template."
        />
      );
    });
    await act(async () => {
      wrapper.find('button').simulate('click');
    });
    expect(copyItem).toHaveBeenCalledTimes(1);
  });
});
