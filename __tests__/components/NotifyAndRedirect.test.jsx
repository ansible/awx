import React from 'react';
import { mountWithContexts } from '../enzymeHelpers';

import { _NotifyAndRedirect } from '../../src/components/NotifyAndRedirect';

describe('<NotifyAndRedirect />', () => {
  test('initially renders succesfully and calls setRootDialogMessage', () => {
    const setRootDialogMessage = jest.fn();
    mountWithContexts(
      <_NotifyAndRedirect
        to="foo"
        setRootDialogMessage={setRootDialogMessage}
        location={{ pathname: 'foo' }}
      />
    );
    expect(setRootDialogMessage).toHaveBeenCalled();
  });
});
