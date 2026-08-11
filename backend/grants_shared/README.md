# Grants Shared

This repo contains the shared code used by the different backend APIs in:
* [Simpler Grants](https://github.com/HHS/simpler-grants-gov)
* [Smarter Grants Management](https://github.com/HHS/smarter-grants-management)

This code is not meant to be used outside of these systems. We cannot provide support for anyone who attempts to use this code for other projects.

[License](https://github.com/HHS/grants-shared/blob/main/LICENSE.md)

## Installation
You can install this package with any python dependency manager.

```shell
# Using pip
pip install grants_shared

# Using poetry
poetry add grants_shared

# Using uv
uv add grants_shared
```

## Release Process

### Version Upgrade

When you make changes, upgrade the version of the package.

```shell
# Upgrade the version with uv
# https://docs.astral.sh/uv/guides/package/#updating-your-version

# Generally do a patch version (eg. 1.0.1 -> 1.0.2)
uv version --bump patch

# Or do a minor version for anything fairly big (eg. 1.1.3 -> 1.2.0)
# uv version --bump minor
```

### Release to PyPi
After your change has been merged to main, you can
publish a new release in PyPi with our [Github action](https://github.com/HHS/grants-shared/actions/workflows/publish-grants-shared-backend.yml)


## Usage
Guidance on common commands and running the application will come in later
versions as we're still getting this setup, but a few basic commands to get you started.

```shell
# Build the docker image
make build

# Run tests
make test

# Formatting and linting
make format
make lint
```


