import { mount } from 'enzyme';

import buildDescription from './buildActivityDescription';

describe('buildActivityStream', () => {
  test('initially renders succesfully', () => {
    const description = mount(buildDescription({}, {}));
    expect(description.find('span').length).toBe(1);
  });
});
