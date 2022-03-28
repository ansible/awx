import {
  renderStateColor,
  renderLabelText,
  renderNodeType,
  renderNodeIcon,
  redirectToDetailsPage,
  getHeight,
  getWidth,
} from './helpers';

describe('renderStateColor', () => {
  test('returns correct node state color', () => {
    expect(renderStateColor('healthy')).toBe('#3E8635');
  });
  test('returns empty string if state is not found', () => {
    expect(renderStateColor('foo')).toBe('');
  });
  test('returns empty string if state is null', () => {
    expect(renderStateColor(null)).toBe('');
  });
  test('returns empty string if state is zero/integer', () => {
    expect(renderStateColor(0)).toBe('');
  });
});
describe('renderNodeType', () => {
  test('returns correct node type', () => {
    expect(renderNodeType('control')).toBe('C');
  });
  test('returns empty string if state is not found', () => {
    expect(renderNodeType('foo')).toBe('');
  });
  test('returns empty string if state is null', () => {
    expect(renderNodeType(null)).toBe('');
  });
  test('returns empty string if state is zero/integer', () => {
    expect(renderNodeType(0)).toBe('');
  });
});
describe('renderNodeIcon', () => {
  test('returns correct node icon', () => {
    expect(renderNodeIcon({ node_type: 'control' })).toBe('C');
  });
  test('returns empty string if state is not found', () => {
    expect(renderNodeIcon('foo')).toBe('');
  });
  test('returns empty string if state is null', () => {
    expect(renderNodeIcon(null)).toBe(false);
  });
  test('returns empty string if state is zero/integer', () => {
    expect(renderNodeIcon(0)).toBe(false);
  });
});
describe('getWidth', () => {
  test('returns 700 if selector is null', () => {
    expect(getWidth(null)).toBe(700);
  });
  test('returns 700 if selector is zero/integer', () => {
    expect(getWidth(0)).toBe(700);
  });
});
describe('getHeight', () => {
  test('returns 600 if selector is null', () => {
    expect(getHeight(null)).toBe(600);
  });
  test('returns 600 if selector is zero/integer', () => {
    expect(getHeight(0)).toBe(600);
  });
});
describe('renderLabelText', () => {
  test('returns label text correctly', () => {
    expect(renderLabelText('error', 'foo')).toBe('! foo');
  });
  test('returns label text if invalid node state is passed', () => {
    expect(renderLabelText('foo', 'bar')).toBe(' bar');
  });
  test('returns empty string if non string params are passed', () => {
    expect(renderLabelText(0, null)).toBe('');
  });
});
describe('redirectToDetailsPage', () => {
  test('returns false if incorrect params are passed', () => {
    expect(redirectToDetailsPage(null, 0)).toBe(false);
  });
});
