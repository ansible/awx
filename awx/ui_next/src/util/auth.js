// eslint-disable-next-line import/prefer-default-export
export function isAuthenticated(cookie) {
  const parsed = `; ${cookie}`.split('; userLoggedIn=');
  if (parsed.length === 2) {
    return (
      parsed
        .pop()
        .split(';')
        .shift() === 'true'
    );
  }
  return false;
}
