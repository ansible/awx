# Releasing AWX (and awx-operator)

The release process for AWX is completely automated as of version 19.5.0.

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

1. navigate to the [Releases page](https://github.com/ansible/awx/releases) for AWX and verify things look ok. The changelog is automatically generated using the [special comment in our Pull Request template](https://github.com/ansible/awx/commit/dc0cc0f910900c506fb6f6ce4366e0e0d1d0ee87).

2. If things look ok, click the pencil icon on the draft:

![Verify draft release](img/verify-draft-release.png)

3. Click "Publish Release":

![Publish release](img/publish-release.png)

Once the release is published, another workflow called [Promote Release](https://github.com/ansible/awx/actions/workflows/promote.yml) will start running:

![Promote release](img/promote-release.png)

This workflow will take the generated images and promote them to quay.io in addition it will also release awxkit and the awx.awx collection. The overall process will not take long.

4. Once the workflow is finished, verify that the new image is present on the [Repository Tags](https://quay.io/repository/ansible/awx?tag=latest&tab=tags) on Quay:

![Verify released AWX image](img/verify-released-awx-image.png)

5. Go to the awx.awx collection on [Ansible Galaxy](https://galaxy.ansible.com/awx/awx) and validate the latest version matches and was updated recently:

![Verify release awx.awx collection](img/galaxy.png)

6. Go to awxkit's page on [PiPy](https://pypi.org/project/awxkit/#history) and validate the latest release is there:

![Verify awxkit](img/pypi.png)

### Releasing the AWX operator

Once the AWX image is live, we can now release the AWX operator.

1. Navigate to the [Releases page](https://github.com/ansible/awx-operator/releases) for AWX operator and follow the same process used for publishing the AWX draft.

Once published, the workflow [Promote AWX Operator image](https://github.com/ansible/awx-operator/actions/workflows/promote.yaml) will run:

![Operator Promotion](img/operator-promote.png)

This workflow will take the generated images and promote them to quay.io.

2. Once complete, verify the image is on the [awx-operator Quay repository](https://quay.io/repository/ansible/awx-operator?tab=tags):

![Verify released awx-operator image](img/verify-released-awx-operator-image.png)
