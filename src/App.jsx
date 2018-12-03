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

class App extends React.Component {
  constructor (props) {
    super(props);

    const isNavOpen = typeof window !== 'undefined' && window.innerWidth >= parseInt(breakpointMd.value, 10);
    this.state = {
      isNavOpen,
      activeGroup: 'views_group',
    };
  }

  onNavSelect = result => {
    this.setState({
      activeGroup: result.groupId
    });
  };

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
    console.log('render');
    const { activeGroup, isNavOpen } = this.state;
    const { logo, loginInfo } = this.props;

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
                    <Nav onSelect={this.onNavSelect} aria-label="Primary Navigation">
                      <NavList>
                        <NavExpandable
                          title="Views"
                          groupId="views_group"
                          isActive={activeGroup === 'views_group'}
                          isExpanded={activeGroup === 'views_group'}
                        >
                          <NavItem
                            to="#/home"
                            groupId="views_group"
                            itemId="views_group_dashboard"
                            isActive={this.expand('home', 'views_group')}
                          >
                            Dashboard
                          </NavItem>
                          <NavItem
                            to="#/jobs"
                            groupId="views_group"
                            itemId="views_group_jobs"
                            isActive={this.expand('jobs', 'views_group')}
                          >
                            Jobs
                          </NavItem>
                          <NavItem
                            to="#/schedules"
                            groupId="views_group"
                            itemId="views_group_schedules"
                            isActive={this.expand('schedules', 'views_group')}
                          >
                            Schedules
                          </NavItem>
                          <NavItem
                            to="#/portal"
                            groupId="views_group"
                            itemId="views_group_portal"
                            isActive={this.expand('portal', 'views_group')}
                          >
                          My View
                          </NavItem>
                        </NavExpandable>
                        <NavExpandable
                          title="Resources"
                          groupId="resources_group"
                          isActive={activeGroup === 'resources_group'}
                          isExpanded={activeGroup === 'resources_group'}
                        >
                          <NavItem
                            to="#/templates"
                            groupId="resources_group"
                            itemId="resources_group_templates"
                            isActive={this.expand('templates', 'resources_group')}
                          >
                            Templates
                          </NavItem>
                          <NavItem
                            to="#/credentials"
                            groupId="resources_group"
                            itemId="resources_group_credentials"
                            isActive={this.expand('credentials', 'resources_group')}
                          >
                            Credentials
                          </NavItem>
                          <NavItem
                            to="#/projects"
                            groupId="resources_group"
                            itemId="resources_group_projects"
                            isActive={this.expand('projects', 'resources_group')}
                          >
                            Projects
                          </NavItem>
                          <NavItem
                            to="#/inventories"
                            groupId="resources_group"
                            itemId="resources_group_inventories"
                            isActive={this.expand('inventories', 'resources_group')}
                          >
                            Inventories
                          </NavItem>
                          <NavItem
                            to="#/inventory_scripts"
                            groupId="resources_group"
                            itemId="resources_group_inventory_scripts"
                            isActive={this.expand('inventory_scripts', 'resources_group')}
                          >
                            Inventory Scripts
                          </NavItem>
                        </NavExpandable>
                        <NavExpandable
                          title="Access"
                          groupId="access_group"
                          isActive={activeGroup === 'access_group'}
                          isExpanded={activeGroup === 'access_group'}
                        >
                          <NavItem
                            to="#/organizations"
                            groupId="access_group"
                            itemId="access_group_organizations"
                            isActive={this.expand('organizations', 'access_group')}
                          >
                            Organizations
                          </NavItem>
                          <NavItem
                            to="#/users"
                            groupId="access_group"
                            itemId="access_group_users"
                            isActive={this.expand('users', 'access_group')}
                          >
                            Users
                          </NavItem>
                          <NavItem
                            to="#/teams"
                            groupId="access_group"
                            itemId="access_group_teams"
                            isActive={this.expand('teams', 'access_group')}
                          >
                            Teams
                          </NavItem>
                        </NavExpandable>
                        <NavExpandable
                          title="Administration"
                          groupId="administration_group"
                          isActive={activeGroup === 'administration_group'}
                          isExpanded={activeGroup === 'administration_group'}
                        >
                          <NavItem
                            to="#/credential_types"
                            groupId="administration_group"
                            itemId="administration_group_credential_types"
                            isActive={this.expand('credential_types', 'administration_group')}
                          >
                            Credential Types
                          </NavItem>
                          <NavItem
                            to="#/notification_templates"
                            groupId="administration_group"
                            itemId="administration_group_notification_templates"
                            isActive={this.expand('notification_templates', 'administration_group')}
                          >
                            Notification Templates
                          </NavItem>
                          <NavItem
                            to="#/management_jobs"
                            groupId="administration_group"
                            itemId="administration_group_management_jobs"
                            isActive={this.expand('management_jobs', 'administration_group')}
                          >
                            Management Jobs
                          </NavItem>
                          <NavItem
                            to="#/instance_groups"
                            groupId="administration_group"
                            itemId="administration_group_instance_groups"
                            isActive={this.expand('instance_groups', 'administration_group')}
                          >
                            Instance Groups
                          </NavItem>
                          <NavItem
                            to="#/applications"
                            groupId="administration_group"
                            itemId="administration_group_applications"
                            isActive={this.expand('applications', 'administration_group')}
                          >
                            Applications
                          </NavItem>
                        </NavExpandable>
                        <NavExpandable
                          title="Settings"
                          groupId="settings_group"
                          isActive={activeGroup === 'settings_group'}
                          isExpanded={activeGroup === 'settings_group'}
                        >
                          <NavItem
                            to="#/auth_settings"
                            groupId="settings_group"
                            itemId="settings_group_auth"
                            isActive={this.expand('auth_settings', 'settings_group')}
                          >
                            Authentication
                          </NavItem>
                          <NavItem
                            to="#/jobs_settings"
                            groupId="settings_group"
                            itemId="settings_group_jobs"
                            isActive={this.expand('jobs_settings', 'settings_group')}
                          >
                            Jobs
                          </NavItem>
                          <NavItem
                            to="#/system_settings"
                            groupId="settings_group"
                            itemId="settings_group_system"
                            isActive={this.expand('system_settings', 'settings_group')}
                          >
                            System
                          </NavItem>
                          <NavItem
                            to="#/ui_settings"
                            groupId="settings_group"
                            itemId="settings_group_ui"
                            isActive={this.expand('ui_settings', 'settings_group')}
                          >
                          User Interface
                          </NavItem>
                        </NavExpandable>
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
