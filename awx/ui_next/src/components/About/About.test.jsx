import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import About from './About';

describe('<About />', () => {
  let aboutWrapper;
  let closeButton;
  const onClose = jest.fn();
  test('initially renders without crashing', () => {
    aboutWrapper = mountWithContexts(<About isOpen onClose={onClose} />);
    expect(aboutWrapper.length).toBe(1);
    aboutWrapper.unmount();
  });

  test('close button calls onClose handler', () => {
    aboutWrapper = mountWithContexts(<About isOpen onClose={onClose} />);
    closeButton = aboutWrapper.find('AboutModalBoxCloseButton Button');
    closeButton.simulate('click');
    expect(onClose).toBeCalled();
    aboutWrapper.unmount();
  });
});
