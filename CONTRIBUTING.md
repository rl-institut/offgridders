## Development

### Prerequisites

- [Git](https://git-scm.com/)


### Philosophy

Development of a feature for this repository should follow the workflow described 
by [Vincent Driessen](https://nvie.com/posts/a-successful-git-branching-model/).

Here are the minimal procedure you should follow : 

#### Step 1: Describe the issue on github

Create [an issue](https://help.github.com/en/articles/creating-an-issue)
on the github repository, describing the problem you will then address
with your feature/fix. This is an important step as it forces one to
think about the issue (to describe an issue to others, one has to think
it through first).

#### Step 2: Solve the issue locally

1. Create a separate branch from `dev`, to work on
    ```bash
    git checkout -b feature/myfeature dev
    ```
    The convention is to always have `feature/` in the branch name. The `myfeature` part should describe shortly what the feature is about (separate words with `-`).
    If you are fixing and error you can replace `feature/` by `fix/`.
2. Try to follow [these conventions](https://chris.beams.io/posts/git-commit) for commit messages:
    - Keep the subject line [short](https://chris.beams.io/posts/git-commit/#limit-50) (i.e. do not commit more than a few changes at the time)
    - Use [imperative](https://chris.beams.io/posts/git-commit/#imperative) for commit messages 
    - Do not end the commit message with a [period](https://chris.beams.io/posts/git-commit/#end) 
        You can use 
        ```bash
        git commit --amend
        ```
        to edit the commit message of your latest commit (provided it is not already pushed on the remote server).
        With `--amend` you can even add/modify changes to the commit.

3. Push your local branch on the remote server `origin`
    ```bash
    git push
    ```
    If your branch does not exist on the remote server yet, git will provide you with instructions, simply follow them.


#### Step 3: Run tests locally

To run tests locally, install the dependencies 
```bash 
pip install -r tests/test_requirements.txt 
```

1. Integration/unit tests 
    ```bash
    pytest tests
    ```
2.  Linting tests
    ```bash
    flake8
    ```
    and
    ```bash
    pylint
    ```
    You can fix the linting errors either manually or with the packages
    `autopep8` or `black` for example.
    
#### Step 4: Submit a pull request (PR)

Follow the [steps](https://help.github.com/en/articles/creating-a-pull-request) of the github help to create the PR.
Please note that you PR should be directed from your branch (for example `myfeature`) towards the branch `dev`.

Add a line `Fix #<number of the issue created in Step 2.0>` in the
description of your PR, so that when it is merged, it automatically
closes the issue once your code gets merged into the default branch of
your repository.
[Here](https://help.github.com/en/github/managing-your-work-on-github/closing-issues-using-keywords)
is a list of other keywords you can use to automatically close the
issues

#### Step 5: Setup continuous integration

To have the test run automatically everytime you push to a pull request
you can add the bash commands under `# command to run tests` of the
`.travis.yml` file. For this you need to have an account by
[Travis](https://travis-ci.org/) and link your repo to their service.
Soon [GitHub action](https://github.com/features/actions) might take
care of this directly within github.

In the `.travis.yml` file are many options commented out, you can have
very complexe schemes to test on many different python versions etc. For
more information look at Travis
[doc](https://docs.travis-ci.com/user/languages/python/) for python.

## Release protocol

Once you are ready to publish a release, branch off from `dev`
    ```bash
    git checkout -b release/vX.Y.Z dev
    ```
For meaning of X, Y and Z version numbers, please refer to this [semantic versioning guidelines](https://semver.org/spec/v2.0.0.html).

In this branch, you should normally only update the version number in the `CHANGELOG.md` and `setup.py` files.

Your `CHANGELOG.md` file could look like this before the release
```
## [unreleased]

### Added
- feature 1
- feature 2
### Changed 
- thing 1
- thing 2
### Removed
- some stuff
```

Simply replace `unreleased` by `X.Y.Z` and add the date of release in [ISO format](https://xkcd.com/1179/), then add the structure for a new `unreleased` version

```
## [unreleased]

### Added
-
### Changed 
-
### Removed
-

## [X.Y.Z] - 20**-**-**
### Added
- feature 1
- feature 2
### Changed 
- thing 1
- thing 2
### Removed
- some stuff
```

After pushing these changes, create a pull request from `release/vX.Y.Z` towards `master` and merge it in `master`.

Locally, merge `release/vX.Y.Z` into `dev`
```
git checkout release/vX.Y.Z
```

```
git pull
```
    
```
git checkout dev
```

```
git merge release/vX.Y.Z
```
And push your these updates to the remote
```
git push
```

The idea behind this procedure is to avoid creating a merge commit in `dev` (because `master` would otherwise have two merge commit for this release once you merge the next release).

Finally, [create a release](https://help.github.com/en/github/administering-a-repository/creating-releases) on github. Please choose master as the target for the tag and format the tag as `vX.Y.Z`. In the description field simply copy-paste the content of the `CHANGELOG`descriptions for this release and you're done!
