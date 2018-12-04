import React, { Fragment } from 'react';
import {
  Redirect,
  Switch,
  withRouter
} from 'react-router-dom';

import {
  BackgroundImage,
  BackgroundImageSrc,
  Nav,
  NavExpandable,
  NavList,
  NavItem,
  Page,
  PageHeader,
  PageSidebar,
  Toolbar,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { global_breakpoint_md as breakpointMd } from '@patternfly/react-tokens';

import api from './api';
import { API_LOGOUT } from './endpoints';

import HelpDropdown from './components/HelpDropdown';
import LogoutButton from './components/LogoutButton';
import TowerLogo from './components/TowerLogo';
import ConditionalRedirect from './components/ConditionalRedirect';

import Applications from './pages/Applications';
import Credentials from './pages/Credentials';
import CredentialTypes from './pages/CredentialTypes';
import Dashboard from './pages/Dashboard';
import InstanceGroups from './pages/InstanceGroups';
import Inventories from './pages/Inventories';
import InventoryScripts from './pages/InventoryScripts';
import Jobs from './pages/Jobs';
import Login from './pages/Login';
import ManagementJobs from './pages/ManagementJobs';
import NotificationTemplates from './pages/NotificationTemplates';
import Organizations from './pages/Organizations';
import Portal from './pages/Portal';
import Projects from './pages/Projects';
import Schedules from './pages/Schedules';
import AuthSettings from './pages/AuthSettings';
import JobsSettings from './pages/JobsSettings';
import SystemSettings from './pages/SystemSettings';
import UISettings from './pages/UISettings';
import License from './pages/License';
import Teams from './pages/Teams';
import Templates from './pages/Templates';
import Users from './pages/Users';

const SideNavItems = ({ items, history }) => {
  const currentPath = history.location.pathname.replace(/^\//, '');
  let activeGroup;
  if (currentPath !== '') {
    [{ groupName: activeGroup }] = items
      .map(({ groupName, routes }) => ({
        groupName,
        paths: routes.map(({ path }) => path)
      }))
      .filter(({ paths }) => paths.indexOf(currentPath) > -1);
  } else {
    activeGroup = 'views';
  }

  return (items.map(({ title, groupName, routes }) => (
    <NavExpandable
      key={groupName}
      title={title}
      groupId={`${groupName}_group`}
      isActive={`${activeGroup}_group` === `${groupName}_group`}
      isExpanded={`${activeGroup}_group` === `${groupName}_group`}
    >
      {routes.map(({ path, title: itemTitle }) => (
        <NavItem
          key={path}
          to={`#/${path}`}
          groupId={`${groupName}_group`}
          isActive={currentPath === path}
        >
          {itemTitle}
        </NavItem>
      ))}
    </NavExpandable>
  )));
};

class App extends React.Component {
  constructor (props) {
    super(props);

    const isNavOpen = typeof window !== 'undefined' && window.innerWidth >= parseInt(breakpointMd.value, 10);
    this.state = {
      isNavOpen
    };
  }

  onNavToggle = () => {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  };

  onLogoClick = () => {
    this.setState({ activeGroup: 'views_group' });
  }

  onDevLogout = async () => {
    console.log('called')
    await api.get(API_LOGOUT);
    this.setState({ activeGroup: 'views_group', activeItem: 'views_group_dashboard' });

    console.log(this.state);
  }

  expand = (path, group) => {
    const { history } = this.props;
    const { activeGroup } = this.state;

    const currentPath = history.location.pathname.split('/')[1];
    if ((path === currentPath) && (group !== activeGroup)) {
      this.setState({ activeGroup: group });
    }
    return (path === currentPath);
  };

  render () {
    const { isNavOpen } = this.state;
    const { logo, loginInfo, history } = this.props;

    const PageToolbar = (
      <Toolbar>
        <ToolbarGroup>
          <ToolbarItem>
            <HelpDropdown />
          </ToolbarItem>
          <ToolbarItem>
            <LogoutButton onDevLogout={() => this.onDevLogout()} />
          </ToolbarItem>
        </ToolbarGroup>
      </Toolbar>
    );

    return (
      <Fragment>
        <BackgroundImage
          src={{
            [BackgroundImageSrc.lg]: '/assets/images/pfbg_1200.jpg',
            [BackgroundImageSrc.md]: '/assets/images/pfbg_992.jpg',
            [BackgroundImageSrc.md2x]: '/assets/images/pfbg_992@2x.jpg',
            [BackgroundImageSrc.sm]: '/assets/images/pfbg_768.jpg',
            [BackgroundImageSrc.sm2x]: '/assets/images/pfbg_768@2x.jpg',
            [BackgroundImageSrc.xl]: '/assets/images/pfbg_2000.jpg',
            [BackgroundImageSrc.xs]: '/assets/images/pfbg_576.jpg',
            [BackgroundImageSrc.xs2x]: '/assets/images/pfbg_576@2x.jpg',
            [BackgroundImageSrc.filter]: '/assets/images/background-filter.svg'
          }}
        />
        <Switch>
          <ConditionalRedirect shouldRedirect={() => api.isAuthenticated()} redirectPath="/" path="/login" component={() => <Login logo={logo} loginInfo={loginInfo} />} />
          <Fragment>
            <Page
              header={(
                <PageHeader
                  logo={<TowerLogo onClick={this.onLogoClick} />}
                  toolbar={PageToolbar}
                  showNavToggle
                  onNavToggle={this.onNavToggle}
                />
              )}
              sidebar={(
                <PageSidebar
                  isNavOpen={isNavOpen}
                  nav={(
                    <Nav aria-label="Primary Navigation">
                      <NavList>
                        <SideNavItems
                          history={history}
                          items={[
                            {
                              groupName: 'views',
                              title: 'Views',
                              routes: [
                                {
                                  path: 'home',
                                  title: 'Dashboard'
                                },
                                {
                                  path: 'jobs',
                                  title: 'Jobs'
                                },
                                {
                                  path: 'schedules',
                                  title: 'Schedules'
                                },
                                {
                                  path: 'portal',
                                  title: 'Portal'
                                },
                              ]
                            },
                            {
                              groupName: 'resources',
                              title: 'Resources',
                              routes: [
                                {
                                  path: 'templates',
                                  title: 'Templates'
                                },
                                {
                                  path: 'credentials',
                                  title: 'Credentials'
                                },
                                {
                                  path: 'projects',
                                  title: 'Projects'
                                },
                                {
                                  path: 'inventories',
                                  title: 'Inventories'
                                },
                                {
                                  path: 'inventory_scripts',
                                  title: 'Inventory Scripts'
                                }
                              ]
                            }
                          ]}
                        />
                      </NavList>
                    </Nav>
                  )}
                />
              )}
              useCondensed
            >
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" exact path="/" component={() => (<Redirect to="/home" />)} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/home" component={Dashboard} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/jobs" component={Jobs} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/schedules" component={Schedules} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/portal" component={Portal} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/templates" component={Templates} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/credentials" component={Credentials} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/projects" component={Projects} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/inventories" component={Inventories} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/inventory_scripts" component={InventoryScripts} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/organizations" component={Organizations} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/users" component={Users} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/teams" component={Teams} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/credential_types" component={CredentialTypes} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/notification_templates" component={NotificationTemplates} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/management_jobs" component={ManagementJobs} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/instance_groups" component={InstanceGroups} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/applications" component={Applications} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/auth_settings" component={AuthSettings} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/jobs_settings" component={JobsSettings} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/system_settings" component={SystemSettings} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/ui_settings" component={UISettings} />
              <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/license" component={License} />
            </Page>
          </Fragment>
        </Switch>
      </Fragment>
    );
  }
}

export default withRouter(App);
