# Community BugScrub tooling

Small python script that automatically distributes PRs and Issues given a list of `people` and dumps the contents in a Spreadsheet.

To be used when distributing the work of reviewing community contributions.

## Usage

Install requirements.

```
pip install -r requirements.txt
```

Get the usage.

```
python generate-sheet.py -h
```

## Adding a github Personal Access Token
The scripts looks first for a github personal access token to use to avoid having the scripts calls rate limited, you can create one or use an existing one if you have. The script looks for the PAT under the environment var `GITHUB_ACCESS_TOKEN`. 


# For internal spreadsheet usage
AWX engineers will need to import the data generated from the script into a spreadshet manager. Please make sure that you do not replace the existing sheets but make a new one or create a new sheet inside the existing spreadsheet upon import. 