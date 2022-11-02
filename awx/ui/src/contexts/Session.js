import React, {
  useContext,
  useEffect,
  useState,
  useRef,
  useCallback,
  useMemo,
} from 'react';
import { useHistory, Redirect } from 'react-router-dom';
import { DateTime } from 'luxon';
import { RootAPI, MeAPI } from 'api';
import { isAuthenticated } from 'util/auth';
import useRequest from 'hooks/useRequest';
import { SESSION_TIMEOUT_KEY, SESSION_USER_ID } from '../constants';

// The maximum supported timeout for setTimeout(), in milliseconds,
// is the highest number you can represent as a signed 32bit
// integer (approximately 25 days)
const MAX_TIMEOUT = 2 ** (32 - 1) - 1;

// The number of seconds the session timeout warning is displayed
// before the user is logged out. Increasing this number (up to
// the total session time, which is 1800s by default) will cause
// the session timeout warning to display sooner.
const SESSION_WARNING_DURATION = 10;

/**
 * The useStorage hook integrates with the browser's localStorage api.
 * It accepts a storage key as its only argument and returns a state
 * variable and setter function for that state variable.
 *
 * This utility behaves much like the standard useState hook with some
 * key differences:
 *   1. You don't pass it an initial value. Instead, the provided key
 *      is used to retrieve the initial value from local storage. If
 *      the key doesn't exist in local storage, null is returned.
 *   2. Behind the scenes, this hook registers an event listener with
 *      the Web Storage api to establish a two-way binding between the
 *      state variable and its corresponding local storage value. This
 *      means that updates to the state variable with the setter
 *      function will produce a corresponding update to the local
 *      storage value and vice-versa.
 *   3. When local storage is shared across browser tabs, the data
 *      binding is also shared across browser tabs. This means that
 *      updates to the state variable using the setter function on
 *      one tab will also update the state variable on any other tab
 *      using this hook with the same key and vice-versa.
 */
function useStorage(key) {
  const [storageVal, setStorageVal] = useState(
    window.localStorage.getItem(key)
  );
  window.addEventListener('storage', () => {
    const newVal = window.localStorage.getItem(key);
    if (newVal !== storageVal) {
      setStorageVal(newVal);
    }
  });
  const setValue = (val) => {
    window.localStorage.setItem(key, JSON.stringify(val));
    setStorageVal(val);
  };
  return [storageVal, setValue];
}

const SessionContext = React.createContext({});
SessionContext.displayName = 'SessionContext';

function SessionProvider({ children }) {
  const history = useHistory();
  const isSessionExpired = useRef(false);
  const sessionTimeoutId = useRef(null);
  const sessionIntervalId = useRef(null);
  const [sessionTimeout, setSessionTimeout] = useStorage(SESSION_TIMEOUT_KEY);
  const [sessionCountdown, setSessionCountdown] = useState(0);
  const [authRedirectTo, setAuthRedirectTo] = useState('/');
  const [isUserBeingLoggedOut, setIsUserBeingLoggedOut] = useState(false);

  const {
    request: fetchLoginRedirectOverride,
    result: { loginRedirectOverride },
    isLoading,
  } = useRequest(
    useCallback(async () => {
      const { data } = await RootAPI.read();
      return {
        loginRedirectOverride: data?.login_redirect_override,
      };
    }, []),
    {
      loginRedirectOverride: null,
      isLoading: true,
    }
  );

  useEffect(() => {
    fetchLoginRedirectOverride();
  }, [fetchLoginRedirectOverride]);

  const logout = useCallback(async () => {
    setIsUserBeingLoggedOut(true);
    if (!isSessionExpired.current) {
      setAuthRedirectTo('/logout');
      window.localStorage.setItem(SESSION_USER_ID, null);
    }
    sessionStorage.clear();
    await RootAPI.logout();
    setSessionTimeout(0);
    setSessionCountdown(0);
    clearTimeout(sessionTimeoutId.current);
    clearInterval(sessionIntervalId.current);
    return <Redirect to="/login" />;
  }, [setSessionTimeout, setSessionCountdown]);

  useEffect(() => {
    if (!isAuthenticated(document.cookie)) {
      return () => {};
    }
    const calcRemaining = () => {
      if (sessionTimeout) {
        return Math.max(
          parseInt(sessionTimeout, 10) - DateTime.now().toMillis(),
          0
        );
      }
      return 0;
    };

    const handleSessionTimeout = () => {
      let countDown = SESSION_WARNING_DURATION;
      setSessionCountdown(countDown);

      sessionIntervalId.current = setInterval(() => {
        if (countDown > 0) {
          setSessionCountdown(--countDown);
        } else {
          isSessionExpired.current = true;
          logout();
        }
      }, 1000);
    };

    setSessionCountdown(0);
    clearTimeout(sessionTimeoutId.current);
    clearInterval(sessionIntervalId.current);

    const calcTimeOut = calcRemaining() - SESSION_WARNING_DURATION * 1000;

    isSessionExpired.current = false;
    sessionTimeoutId.current = setTimeout(
      handleSessionTimeout,
      calcTimeOut <= 0 ? MAX_TIMEOUT : Math.min(calcTimeOut, MAX_TIMEOUT)
    );

    return () => {
      clearTimeout(sessionTimeoutId.current);
      clearInterval(sessionIntervalId.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [history, sessionTimeout]);

  const handleSessionContinue = useCallback(async () => {
    await MeAPI.read();
    setSessionCountdown(0);
    clearTimeout(sessionTimeoutId.current);
    clearInterval(sessionIntervalId.current);
  }, []);

  const sessionValue = useMemo(
    () => ({
      authRedirectTo,
      handleSessionContinue,
      isSessionExpired,
      isUserBeingLoggedOut,
      loginRedirectOverride,
      logout,
      sessionCountdown,
      setAuthRedirectTo,
    }),
    [
      authRedirectTo,
      handleSessionContinue,
      isSessionExpired,
      isUserBeingLoggedOut,
      loginRedirectOverride,
      logout,
      sessionCountdown,
      setAuthRedirectTo,
    ]
  );

  if (isLoading) {
    return null;
  }

  return (
    <SessionContext.Provider value={sessionValue}>
      {children}
    </SessionContext.Provider>
  );
}

function useSession() {
  const context = useContext(SessionContext);
  if (context === undefined) {
    throw new Error('useSession must be used within a SessionProvider');
  }
  return context;
}

export { SessionContext, SessionProvider, useSession };
