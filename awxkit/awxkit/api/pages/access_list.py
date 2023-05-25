from awxkit.api.resources import resources
from . import users
from . import page


class AccessList(page.PageList, users.User):
    pass


page.register_page(
    [
        resources.organization_access_list,
        resources.user_access_list,
        resources.inventory_access_list,
        resources.group_access_list,
        resources.credential_access_list,
        resources.project_access_list,
        resources.job_template_access_list,
        resources.team_access_list,
    ],
    AccessList,
)
