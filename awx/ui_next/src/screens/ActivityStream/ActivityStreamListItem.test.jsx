import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ActivityStreamListItem from './ActivityStreamListItem';

jest.mock('../../api/models/ActivityStream');

describe('<ActivityStreamListItem />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <table>
        <tbody>
          <ActivityStreamListItem
            streamItem={{
              timestamp: '12:00:00',
            }}
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
  });
});
