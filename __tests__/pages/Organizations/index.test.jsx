import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import Organizations from '../../../src/pages/Organizations/index';

describe('<Organizations />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <I18nProvider>
          <Organizations
            match={{ path: '/organizations', url: '/organizations' }}
            location={{ search: '', pathname: '/organizations' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });
});
