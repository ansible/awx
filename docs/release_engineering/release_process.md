# Releasing AWX (and awx-operator)

The release process for AWX is completely automated as of version 19.5.0.

If you need to revert a release, please refer to the [Revert a Release](#revert-a-release) section.
## Get latest release version and list of new work

1. Open the main project page for [AWX](https://github.com/ansible/awx/releases) and [AWX Operator](https://github.com/ansible/awx-operator/releases).

Find the latest releases of the projects on the right hand side of the screen:

![Latest Release](img/latest-release.png)

2. Open the compare screen for the two projects [AWX](https://github.com/ansible/awx/compare) and [AWX Operator](https://github.com/ansible/awx-operator/compare).
In the two dropdowns near the top of the page leave the `compare` menu at devel and select the drop down for `base` and then select `tags` and finally select the latest release from step 1:

![PR Compare Screen](img/compare-screen.png)

The page will now automatically update with a list of PRs that are in `AWX/devel` but not in the last release.

![PR Compare List](img/pr_compare_list.png)

## Select the next release version

Use this list of PRs to decide if this is a X-stream (major) release, Y-stream (minor) release, or a Z-stream (patch) release. Use [semver](https://semver.org/#summary) to help determine what kind of release is needed.

Indicators of a Z-stream release:

- No significant new features have been merged into devel since the last release.

Indicators of a Y-stream release:

- Additional features, non disrupting change of subcomponents.

Indicators of an X-stream release:

- Disruptive changes.

If the latest release of `AWX` is 19.5.0:

- X-stream release version will be 20.0.0.
- Y-stream release version will be 19.6.0.
- Z-stream release version will be 19.5.1.

With very few exceptions the new `AWX Operator` release will always be a Y-stream release.

## Stage the release

To stage the release, maintainers of this repository can run the [Stage Release](https://github.com/ansible/awx/actions/workflows/stage.yml) workflow.

The link above will take you directly to the flow execution; if you wanted to manually navigate to the screen:

1. Click "Actions" at the top of GitHub.
2. Click on the "Stage Release" workflow.

Once you are on the Stage Release workflow page:

3. Click the "Run Workflow" drop down.
4. Populate the inputs.
5. Click the "Run workflow" button.

![Staging AWX](img/stage-release.png)

This workflow will:

- Build awx from devel
- Build awx-operator from devel
- Run smoke tests
- Create a draft release for both `ansible/awx` and `ansible/awx-operator`

## Promote the draft releases

### Releasing AWX, awxkit and awx.awx collection

Once staging is complete we can complete the release of awx and the operator.

1. navigate to the [Releases page](https://github.com/ansible/awx/releases) for AWX and verify things look ok.

2. Click the pencil icon on the draft:

![Verify draft release](img/verify-draft-release.png)

3. Click the generate release notes button (turns grey after clicking once)

4. Add in a message of what operator version is release with this AWX version (if applicable):
```
## AWX Operator
Released with AWX Operator v0.23.0
```

5. Click "Publish Release":

![Publish release](img/publish-release.png)

Once the release is published, another workflow called [Promote Release](https://github.com/ansible/awx/actions/workflows/promote.yml) will start running:

![Promote release](img/promote-release.png)

This workflow will take the generated images and promote them to quay.io in addition it will also release awxkit and the awx.awx collection. The overall process will not take long.

6. Once the workflow is finished, verify that the new image is present on the [Repository Tags](https://quay.io/repository/ansible/awx?tag=latest&tab=tags) on Quay:

![Verify released AWX image](img/verify-released-awx-image.png)

7. Go to the awx.awx collection on [Ansible Galaxy](https://galaxy.ansible.com/awx/awx) and validate the latest version matches and was updated recently:

![Verify release awx.awx collection](img/galaxy.png)

8. Go to awxkit's page on [PiPy](https://pypi.org/project/awxkit/#history) and validate the latest release is there:

![Verify awxkit](img/pypi.png)

### Releasing the AWX operator

Once the AWX image is live, we can now release the AWX operator.

1. Navigate to the [Releases page](https://github.com/ansible/awx-operator/releases) for AWX operator and follow the same process used for publishing the AWX draft except note the version of AWX released with Operator.

Once published, the workflow [Promote AWX Operator image](https://github.com/ansible/awx-operator/actions/workflows/promote.yaml) will run:

![Operator Promotion](img/operator-promote.png)

This workflow will take the generated images and promote them to quay.io.

2. Once complete, verify the image is on the [awx-operator Quay repository](https://quay.io/repository/ansible/awx-operator?tab=tags):

![Verify released awx-operator image](img/verify-released-awx-operator-image.png)

## Notify the AWX mailing list
Send an email to the [AWX Mailing List](mailto:awx-project@googlegroups.com) with a message format of type "AWX Release" from the [mailing list triage standard replies](../.github/triage_replies.md#awx-release)

## Send an IRC message over matrix to #social:ansible.com for bullhorn:

@newsbot
We're happy to announce that [AWX version 21.1.0](https://github.com/ansible/awx/releases/tag/21.1.0) is now available!
We're happy to announce that [AWX Operator version 0.22.0](https://github.com/ansible/awx-operator/releases/tag/0.22.0) is now available!

## Send the same IRC message (less the @newsbot) to #awx:ansible.com

## Revert a Release

Decide whether or not you can just fall-forward with a new AWX Release to fix a bad release. If you need to remove published artifacts from publically facing repositories, follow the steps below.

Here are the steps needed to revert an AWX and an AWX-Operator release. Depending on your use case, follow the steps for reverting just an AWX release, an Operator release or both.


1. Navigate to the [AWX Release Page](https://github.com/ansible/awx/releases) and delete the AWX Release that needs to be removed.

![Revert-1-Image](img/revert-1.png)

2. Navigate to the [AWX Tags Page](https://github.com/ansible/awx/tags) and delete the AWX Tag that got created by the Github Actions Workflow from when you originally tried to release AWX. You need delete the release in step 1 before you can do this step. The tag must not be tied to a release if you want to delete a tag.

![Tag-Revert-1-Image](img/tag-revert-1.png)
[comment]: <> (Need an image here for actually deleting an orphaned tag, place here during next release)

3. Navigate to the [AWX Operator Release Page]() and delete the AWX-Operator release that needss to tbe removed.

![Revert-2-Image](img/revert-2.png)

4. Navigate to [quay.io](https://quay.io/repository/ansible/awx?tag=latest&tab=tags) and delete the published AWX image(s) and tags.

5. Navigate to [quay.io](https://github.com/ansible/awx-operator/releases) and delete the published AWX Operator image(s) and tags.

6. Navigate to the [Ansible Galaxy Collections](https://galaxy.ansible.com/awx/awx) website and remove the published AWX collection with the bad tag.

7. Navigate to the [PyPi](https://pypi.org/project/awxkit/#history) and delete the bad AWX tag and release that got published.

8. [Restart the Release Process](#releasing-awx-and-awx-operator)