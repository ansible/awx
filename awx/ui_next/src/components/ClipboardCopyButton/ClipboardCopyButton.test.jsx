import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ClipboardCopyButton from './ClipboardCopyButton';

describe('ClipboardCopyButton', () => {
  beforeEach(() => {
    document.execCommand = jest.fn();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders the expected content', () => {
    const wrapper = mountWithContexts(
      <ClipboardCopyButton
        clickTip="foo"
        hoverTip="bar"
        copyTip="baz"
        copiedSuccessTip="qux"
        stringToCopy="foobar!"
        isDisabled={false}
      />
    );
    expect(wrapper).toHaveLength(1);
  });
  test('clicking button calls execCommand to copy to clipboard', async () => {
    const mockDelay = 1;
    const wrapper = mountWithContexts(
      <ClipboardCopyButton
        clickTip="foo"
        hoverTip="bar"
        copyTip="baz"
        copiedSuccessTip="qux"
        stringToCopy="foobar!"
        isDisabled={false}
        switchDelay={mockDelay}
      />
    ).find('ClipboardCopyButton');
    expect(wrapper.state('copied')).toBe(false);
    wrapper.find('Button').simulate('click');
    expect(document.execCommand).toBeCalledWith('copy');
    expect(wrapper.state('copied')).toBe(true);
    await new Promise(resolve => setTimeout(resolve, mockDelay));
    wrapper.update();
    expect(wrapper.state('copied')).toBe(false);
  });
  test('should render disabled button', () => {
    const wrapper = mountWithContexts(
      <ClipboardCopyButton
        clickTip="foo"
        hoverTip="bar"
        copyTip="baz"
        copiedSuccessTip="qux"
        stringToCopy="foobar!"
        isDisabled
      />
    );
    expect(wrapper.find('Button').prop('isDisabled')).toBe(true);
  });
});
