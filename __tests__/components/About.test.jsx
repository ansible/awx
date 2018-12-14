import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import api from '../../src/api';
import { API_CONFIG } from '../../src/endpoints';
import About from '../../src/components/About';

describe('<About />', () => {
  let aboutWrapper;
  let closeButton;

  test('initially renders without crashing', () => {
    aboutWrapper = mount(
      <I18nProvider>
        <About isOpen />
      </I18nProvider>
    );
    expect(aboutWrapper.length).toBe(1);
    aboutWrapper.unmount();
  });

  test('close button calls onAboutModalClose', () => {
    const onAboutModalClose = jest.fn();
    aboutWrapper = mount(
      <I18nProvider>
        <About isOpen onAboutModalClose={onAboutModalClose} />
      </I18nProvider>
    );
    closeButton = aboutWrapper.find('AboutModalBoxCloseButton Button');
    closeButton.simulate('click');
    expect(onAboutModalClose).toBeCalled();
    aboutWrapper.unmount();
  });

  test('sets error on api request failure', async () => {
    api.get = jest.fn().mockImplementation(() => {
      const err = new Error('404 error');
      err.response = { status: 404, message: 'problem' };
      return Promise.reject(err);
    });
    aboutWrapper = mount(
      <I18nProvider>
        <About isOpen />
      </I18nProvider>
    );

    const aboutComponentInstance = aboutWrapper.find(About).instance();
    await aboutComponentInstance.componentDidMount();
    expect(aboutComponentInstance.state.error.response.status).toBe(404);
    aboutWrapper.unmount();
  });

  test('API Config endpoint is valid', () => {
    expect(API_CONFIG).toBeDefined();
  });
});
