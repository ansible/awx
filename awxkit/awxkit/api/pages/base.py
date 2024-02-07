import collections
import logging

from requests.auth import HTTPBasicAuth

from awxkit.api.pages import Page, get_registered_page, exception_from_status_code
from awxkit.config import config
from awxkit.api.resources import resources
import awxkit.exceptions as exc


log = logging.getLogger(__name__)


class Base(Page):
    def silent_delete(self):
        """Delete the object. If it's already deleted, ignore the error"""
        try:
            if not config.prevent_teardown:
                return self.delete()
        except (exc.NoContent, exc.NotFound, exc.Forbidden):
            pass
        except (exc.BadRequest, exc.Conflict) as e:
            if 'Job has not finished processing events' in e.msg:
                pass
            if 'Resource is being used' in e.msg:
                pass
            else:
                raise e

    def get_object_role(self, role, by_name=False):
        """Lookup and return a related object role by its role field or name.

        Args:
        ----
            role (str): The role's `role_field` or name
            by_name (bool): Whether to retrieve the role by its name field (default: False)

        Examples:
        --------
            >>> # get the description of the Use role for an inventory
            >>> inventory = v2.inventory.create()
            >>> use_role_1 = inventory.get_object_role('use_role')
            >>> use_role_2 = inventory.get_object_role('use', True)
            >>> use_role_1.description
            u'Can use the inventory in a job template'
            >>> use_role_1.json == use_role_2.json
            True

        """
        if by_name:
            for obj_role in self.related.object_roles.get().results:
                if obj_role.name.lower() == role.lower():
                    return obj_role

            raise Exception("Role '{0}' not found for {1.endpoint}".format(role, self))

        object_roles = self.get_related('object_roles', role_field=role)
        if not object_roles.count == 1:
            raise Exception("No role with role_field '{0}' found.".format(role))
        return object_roles.results[0]

    def set_object_roles(self, agent, *role_names, **kw):
        """Associate related object roles to a User or Team by role names

        Args:
        ----
            agent (User or Team): The agent the role is to be (dis)associated with.
            *role_names (str): an arbitrary number of role names ('Admin', 'Execute', 'Read', etc.)
            **kw:
                endpoint (str): The endpoint to use when making the object role association
                - 'related_users': use the related users endpoint of the role (default)
                - 'related_roles': use the related roles endpoint of the user
                disassociate (bool): Indicates whether to disassociate the role with the user (default: False)

        Examples:
        --------
            # create a user that is an organization admin with use and
            # update roles on an inventory
            >>> organization = v2.organization.create()
            >>> inventory = v2.inventory.create()
            >>> user = v2.user.create()
            >>> organization.set_object_roles(user, 'admin')
            >>> inventory.set_object_roles(user, 'use', 'update')

        """
        from awxkit.api.pages import User, Team

        endpoint = kw.get('endpoint', 'related_users')
        disassociate = kw.get('disassociate', False)

        if not any([isinstance(agent, agent_type) for agent_type in (User, Team)]):
            raise ValueError('Invalid agent type {0.__class__.__name__}'.format(agent))

        if endpoint not in ('related_users', 'related_roles'):
            raise ValueError('Invalid role association endpoint: {0}'.format(endpoint))

        object_roles = [self.get_object_role(name, by_name=True) for name in role_names]
        payload = {}
        for role in object_roles:
            if endpoint == 'related_users':
                payload['id'] = agent.id
                if isinstance(agent, User):
                    endpoint_model = role.related.users
                elif isinstance(agent, Team):
                    endpoint_model = role.related.teams
                else:
                    raise RuntimeError("Unhandled type for agent: {0.__class__.__name__}.".format(agent))
            elif endpoint == 'related_roles':
                payload['id'] = role.id
                endpoint_model = agent.related.roles
            else:
                raise RuntimeError('Invalid role association endpoint')

            if disassociate:
                payload['disassociate'] = True

            try:
                endpoint_model.post(payload)
            except exc.NoContent:  # desired exception on successful (dis)association
                pass
        return True

    @property
    def object_roles(self):
        from awxkit.api.pages import Roles, Role

        url = self.get().json.related.object_roles
        for obj_role in Roles(self.connection, endpoint=url).get().json.results:
            yield Role(self.connection, endpoint=obj_role.url).get()

    def get_authtoken(self, username='', password=''):
        default_cred = config.credentials.default
        payload = dict(username=username or default_cred.username, password=password or default_cred.password)
        auth_url = resources.authtoken
        return get_registered_page(auth_url)(self.connection, endpoint=auth_url).post(payload).token

    def load_authtoken(self, username='', password=''):
        self.connection.login(token=self.get_authtoken(username, password))
        return self

    load_default_authtoken = load_authtoken

    def get_oauth2_token(self, username='', password='', client_id=None, description='AWX CLI', client_secret=None, scope='write'):
        default_cred = config.credentials.default
        username = username or default_cred.username
        password = password or default_cred.password
        req = collections.namedtuple('req', 'headers')({})
        if client_id and client_secret:
            HTTPBasicAuth(client_id, client_secret)(req)
            req.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            resp = self.connection.post(
                f"{config.api_base_path}o/token/",
                data={"grant_type": "password", "username": username, "password": password, "scope": scope},
                headers=req.headers,
            )
        elif client_id:
            req.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            resp = self.connection.post(
                f"{config.api_base_path}o/token/",
                data={"grant_type": "password", "username": username, "password": password, "client_id": client_id, "scope": scope},
                headers=req.headers,
            )
        else:
            HTTPBasicAuth(username, password)(req)
            resp = self.connection.post(
                '{0}v2/users/{1}/personal_tokens/'.format(config.api_base_path, username),
                json={"description": description, "application": None, "scope": scope},
                headers=req.headers,
            )
        if resp.ok:
            result = resp.json()
            if client_id:
                return result.pop('access_token', None)
            else:
                return result.pop('token', None)
        else:
            raise exception_from_status_code(resp.status_code)

    def load_session(self, username='', password=''):
        default_cred = config.credentials.default
        self.connection.login(
            username=username or default_cred.username, password=password or default_cred.password, **self.connection.get_session_requirements()
        )
        return self

    def cleanup(self):
        log.debug('{0.endpoint} cleaning up.'.format(self))
        return self._cleanup(self.delete)

    def silent_cleanup(self):
        log.debug('{0.endpoint} silently cleaning up.'.format(self))
        return self._cleanup(self.silent_delete)

    def _cleanup(self, delete_method):
        try:
            delete_method()
        except exc.Forbidden as e:
            if e.msg == {'detail': 'Cannot delete running job resource.'}:
                self.cancel()
                self.wait_until_completed(interval=1, timeout=30, since_job_created=False)
                delete_method()
            else:
                raise
        except exc.Conflict as e:
            conflict = e.msg.get('conflict', e.msg.get('error', ''))
            if "running jobs" in conflict:
                active_jobs = e.msg.get('active_jobs', [])  # [{type: id},], not page containing
                jobs = []
                for active_job in active_jobs:
                    job_type = active_job['type']
                    endpoint = '{}v2/{}s/{}/'.format(config.api_base_path, job_type, active_job['id'])
                    job = self.walk(endpoint)
                    jobs.append(job)
                    job.cancel()
                for job in jobs:
                    job.wait_until_completed(interval=1, timeout=30, since_job_created=False)
                delete_method()
            else:
                raise
