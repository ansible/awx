/**
 * The debounce utility creates a debounced version of the provided
 * function. The debounced function delays invocation until after
 * the given time interval (milliseconds) has elapsed since the last
 * time the function was called. This means that if you call the
 * debounced function repeatedly, it will only run once after it
 * stops being called.
 */
const debounce = (func, interval) => {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      func(...args);
    }, interval);
  };
};

export default debounce;
