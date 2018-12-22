import React, { Fragment } from 'react';
import { ConfigContext } from './context';

import { I18nProvider, I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Redirect,
  Switch,
  withRouter
} from 'react-router-dom';

import {
  BackgroundImage,
  BackgroundImageSrc,
  Nav,
  NavList,
  Page,
  PageHeader,
  PageSidebar,
  Toolbar,
  ToolbarGroup,
  ToolbarItem
} from '@patternfly/react-core';
import { global_breakpoint_md as breakpointMd } from '@patternfly/react-tokens';

import api from './api';
import { API_LOGOUT, API_CONFIG } from './endpoints';

import HelpDropdown from './components/HelpDropdown';
import LogoutButton from './components/LogoutButton';
import TowerLogo from './components/TowerLogo';
import ConditionalRedirect from './components/ConditionalRedirect';
import NavExpandableGroup from './components/NavExpandableGroup';

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

import ja from '../build/locales/ja/messages';
import en from '../build/locales/en/messages';

const catalogs = { en, ja };

// This spits out the language and the region.  Example: es-US
const language = (navigator.languages && navigator.languages[0])
  || navigator.language
  || navigator.userLanguage;

const languageWithoutRegionCode = language.toLowerCase().split(/[_-]+/)[0];


class App extends React.Component {
  constructor(props) {
    super(props);

    const isNavOpen = typeof window !== 'undefined' && window.innerWidth >= parseInt(breakpointMd.value, 10);
    this.state = {
      isNavOpen,
      config: {},
      error: false,
    };
  }

  onNavToggle = () => {
    this.setState(({ isNavOpen }) => ({ isNavOpen: !isNavOpen }));
  };

  onLogoClick = () => {
    this.setState({ activeGroup: 'views_group' });
  }

  onDevLogout = async () => {
    await api.get(API_LOGOUT);
    this.setState({ activeGroup: 'views_group', activeItem: 'views_group_dashboard' });
  }

  async componentDidMount() {
    // Grab our config data from the API and store in state
    try {
      const { data } = await api.get(API_CONFIG);
      this.setState({ config: data });
    } catch (error) {
      this.setState({ error });
    }
  }

  render() {
    const { isNavOpen, config } = this.state;
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
      <I18nProvider language={languageWithoutRegionCode} catalogs={catalogs}>
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
            <ConditionalRedirect
              shouldRedirect={() => api.isAuthenticated()}
              redirectPath="/"
              path="/login"
              component={() => <Login logo={logo} loginInfo={loginInfo} />}
            />
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
                      <I18n>
                        {({ i18n }) => (
                          <Nav aria-label={i18n._(t`Primary Navigation`)}>
                            <NavList>
                              <NavExpandableGroup
                                groupId="views_group"
                                title={i18n._("Views")}
                                routes={[
                                  { path: '/home', title: i18n._('Dashboard') },
                                  { path: '/jobs', title: i18n._('Jobs') },
                                  { path: '/schedules', title: i18n._('Schedules') },
                                  { path: '/portal', title: i18n._('Portal Mode') },
                                ]}
                              />
                              <NavExpandableGroup
                                groupId="resources_group"
                                title={i18n._("Resources")}
                                routes={[
                                  { path: '/templates', title: i18n._('Templates') },
                                  { path: '/credentials', title: i18n._('Credentials') },
                                  { path: '/projects', title: i18n._('Projects') },
                                  { path: '/inventories', title: i18n._('Inventories') },
                                  { path: '/inventory_scripts', title: i18n._('Inventory Scripts') }
                                ]}
                              />
                              <NavExpandableGroup
                                groupId="access_group"
                                title={i18n._("Access")}
                                routes={[
                                  { path: '/organizations', title: i18n._('Organizations') },
                                  { path: '/users', title: i18n._('Users') },
                                  { path: '/teams', title: i18n._('Teams') }
                                ]}
                              />
                              <NavExpandableGroup
                                groupId="administration_group"
                                title={i18n._("Administration")}
                                routes={[
                                  { path: '/credential_types', title: i18n._('Credential Types') },
                                  { path: '/notification_templates', title: i18n._('Notifications') },
                                  { path: '/management_jobs', title: i18n._('Management Jobs') },
                                  { path: '/instance_groups', title: i18n._('Instance Groups') },
                                  { path: '/applications', title: i18n._('Integrations') }
                                ]}
                              />
                              <NavExpandableGroup
                                groupId="settings_group"
                                title={i18n._("Settings")}
                                routes={[
                                  { path: '/auth_settings', title: i18n._('Authentication') },
                                  { path: '/jobs_settings', title: i18n._('Jobs') },
                                  { path: '/system_settings', title: i18n._('System') },
                                  { path: '/ui_settings', title: i18n._('User Interface') },
                                  { path: '/license', title: i18n._('License') }
                                ]}
                              />
                            </NavList>
                          </Nav>
                        )}
                      </I18n>
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
                <ConfigContext.Provider value={config}>
                  <ConditionalRedirect shouldRedirect={() => !api.isAuthenticated()} redirectPath="/login" path="/organizations" component={Organizations} />
                </ConfigContext.Provider>
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
      </I18nProvider>
    );
  }
}

export default withRouter(App);
