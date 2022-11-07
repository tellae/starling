# Starling contributing guidelines

## Introduction

Thank you for considering contributing to Starling ! 

Reading these guidelines eases the interactions between the project owners and the contributors - you !

We would love to see you contribute to make Starling a better project ! 
There are many ways to contribute, from writing tutorials or blog posts, improving the documentation, 
submitting bug reports and feature requests or writing code which can be incorporated into Starling itself.

Please don't use the issue tracker for support questions. Prefer sending us a mail at starling@tellae.fr

## Getting started

#### If you find a security vulnerability:

  - do NOT open an issue. Email starling@tellae.fr instead

#### If you've found a bug:

  - read the error message and [documentation](https://starling.readthedocs.io/en/latest/)
  - search through the [project issues](https://github.com/tellae/starling/issues?q=is%3Aissue++)
  - if the problem is with a dependency of this project, open an issue in the dependency's repo
  - if the problem is with Starling and you can fix it simply, please open a pull request
  - if the problem persists, please open an issue in the [issue tracker](https://github.com/tellae/starling/issues), including a minimal working example so others can independently and completely reproduce the problem

#### If you have a feature proposal or want to contribute:

  - post your proposal on the [issue tracker](https://github.com/tellae/starling/issues) so we can review it together
  - fork the repo, make your change, test it, and submit a PR (do NOT merge the PR yourself)
  - respond to code review
  - adhere to the project code standards (see below)

## Coding style and commit messages
    
#### Coding style

The coding style imposed on Starling includes:

  - respect [PEP8 style guide](https://peps.python.org/pep-0008/) as much as possible
  - [black](https://black.readthedocs.io/en/stable/) code style with max line length of 100
  - write code in english
  - use [Python typing](https://docs.python.org/3/library/typing.html) when possible
  - reST docstring style (for [Sphinx](https://www.sphinx-doc.org/en/master/index.html) documentation). Example: 

```python
def function(param1: str, param2: int):
    """
    This is a reST style.
    
    :param param1: this is a first param
    :param param2: this is a second param
    :returns: this is a description of what is returned
    :raises keyError: raises an exception
    """
    return param1, param2
```


#### Commit message convention

Commits on branch `main` must use the [conventional commit convention](https://www.conventionalcommits.org/en/v1.0.0/)
in order to generate a [changelog from the commits](https://github.com/conventional-changelog/standard-version)
