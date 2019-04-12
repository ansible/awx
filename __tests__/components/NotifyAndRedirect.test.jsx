import React from 'react';
import { mount } from 'enzyme';

import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { _NotifyAndRedirect } from '../../src/components/NotifyAndRedirect';

describe('<NotifyAndRedirect />', () => {
  test('initially renders succesfully and calls setRootDialogMessage', () => {
    const setRootDialogMessage = jest.fn();
    mount(
      <MemoryRouter>
        <I18nProvider>
          <_NotifyAndRedirect
            to="foo"
            setRootDialogMessage={setRootDialogMessage}
            location={{ pathname: 'foo' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
    expect(setRootDialogMessage).toHaveBeenCalled();
  });
});
