// eslint-disable-next-line import/prefer-default-export
export function isAuthenticated(cookie) {
  const parsed = `; ${cookie}`.split('; userLoggedIn=');
  if (parsed.length === 2) {
    return parsed.pop().split(';').shift() === 'true';
  }
  return false;
}

export function getCurrentUserId(cookie) {
  if (!isAuthenticated(cookie)) {
    return null;
  }
  const name = 'current_user';
  let userId = null;
  if (cookie && cookie !== '') {
    const cookies = cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const parsedCookie = cookies[i].trim();
      if (parsedCookie.substring(0, name.length + 1) === `${name}=`) {
        userId = parseUserId(
          decodeURIComponent(parsedCookie.substring(name.length + 1))
        );
        break;
      }
    }
  }
  return userId;
}

function parseUserId(decodedUserData) {
  const userData = JSON.parse(decodedUserData);
  return userData.id;
}
