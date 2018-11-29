const getTabName = (tab) => {
  let tabName = '';
  if (tab === 'details') {
    tabName = 'Details';
  } else if (tab === 'users') {
    tabName = 'Users';
  } else if (tab === 'teams') {
    tabName = 'Teams';
  } else if (tab === 'admins') {
    tabName = 'Admins';
  } else if (tab === 'notifications') {
    tabName = 'Notifications';
  }
  return tabName;
};

export default getTabName;
