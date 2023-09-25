
What should I work on?
=======================

Good first issue
-----------------

We have a `"good first issue" label` <https://github.com/ansible/awx/issues?q=is%3Aopen+label%3A%22good+first+issue%22+label%3Acomponent%3Adocs+) we put on some doc issues that might be a good starting point for new contributors with the following filter:

::

	is:open label:"good first issue" label:component:docs 


Fixing and updating the documentation are always appreciated, so reviewing the backlog of issues is always a good place to start.


Things to know prior to submitting revisions
----------------------------------------------

- All doc revisions or additions are done through pull requests against the ``devel`` branch.
- You must use ``git commit --signoff`` for any commit to be merged, and agree that usage of ``--signoff`` constitutes agreement with the terms of `DCO 1.1 <https://github.com/ansible/awx/blob/devel/DCO_1_1.md>`_.
- Take care to make sure no merge commits are in the submission, and use ``git rebase`` vs ``git merge`` for this reason.
  - If collaborating with someone else on the same branch, consider using ``--force-with-lease`` instead of ``--force``. This will prevent you from accidentally overwriting commits pushed by someone else. For more information, see `git push docs <https://git-scm.com/docs/git-push#git-push---force-with-leaseltrefnamegt>`_.
- If submitting a large doc change, it's a good idea to join the `Ansible Forum <https://forum.ansible.com/tag/documentation>`_, and talk about what you would like to do or add first. This not only helps everyone know what's going on, it also helps save time and effort, if the community decides some changes are needed.
- We ask all of our community members and contributors to adhere to the `Ansible code of conduct <http://docs.ansible.com/ansible/latest/community/code_of_conduct.html>`_. If you have questions, or need assistance, please reach out to our community team at `codeofconduct@ansible.com <mailto:codeofconduct@ansible.com>`_.


.. Note::

	- Issue assignment will only be done for maintainers of the project. If you decide to work on an issue, please feel free to add a comment in the issue to let others know that you are working on it; but know that we will accept the first pull request from whomever is able to fix an issue. Once your PR is accepted we can add you as an assignee to an issue upon request. 

	- If you work in a part of the docs that is going through active development, your changes may be rejected, or you may be asked to `rebase`. A good idea before starting work is to have a discussion with us and ask questions on Matrix at `#awx:ansible.com <https://matrix.to/#/#awx:ansible.com>`_ or discuss your ideas on the `Ansible Forum <https://forum.ansible.com/tag/documentation>`_.

	- If you find an issue with the functions of the UI or API, please see the `Reporting Issues <https://github.com/ansible/awx/blob/devel/CONTRIBUTING.md#reporting-issues>`_ section to open an issue. 

	- If you find an issue with the docs themselves, refer to :ref:`docs_report_issues`.


Translations
-------------

At this time we do not accept PRs for adding additional language translations as we have an automated process for generating our translations. This is because translations require constant care as new strings are added and changed in the code base. Because of this the .po files are overwritten during every translation release cycle. We also can't support a lot of translations on AWX as its an open source project and each language adds time and cost to maintain. If you would like to see AWX translated into a new language please create an issue and ask others you know to upvote the issue. Our translation team will review the needs of the community and see what they can do around supporting additional language.

If you find an issue with an existing translation, please see the `Reporting Issues <https://github.com/ansible/awx/blob/devel/CONTRIBUTING.md#reporting-issues>`_ section to open an issue and our translation team will work with you on a resolution. 
