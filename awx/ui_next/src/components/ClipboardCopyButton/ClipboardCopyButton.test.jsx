import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ClipboardCopyButton from './ClipboardCopyButton';

document.execCommand = jest.fn();

jest.useFakeTimers();

describe('ClipboardCopyButton', () => {
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
  test('clicking button calls execCommand to copy to clipboard', () => {
    const wrapper = mountWithContexts(
      <ClipboardCopyButton
        clickTip="foo"
        hoverTip="bar"
        copyTip="baz"
        copiedSuccessTip="qux"
        stringToCopy="foobar!"
        isDisabled={false}
      />
    ).find('ClipboardCopyButton');
    expect(wrapper.state('copied')).toBe(false);
    wrapper.find('Button').simulate('click');
    expect(document.execCommand).toBeCalledWith('copy');
    expect(wrapper.state('copied')).toBe(true);
    jest.runAllTimers();
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
