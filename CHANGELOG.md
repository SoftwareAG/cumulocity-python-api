# Changelog


## Work in progress

### Changed

* Added this changelog :-)

* Fixed [Issue #7](https://github.com/SoftwareAG/cumulocity-python-api/issues/7):
  Improved caching and user experience when creating CumulocityApp instances. Added unit tests.

* Added possibility to resolve the tenant ID from authorization headers (both `Basic` and `Bearer`).


## Version 1.0.1

### Changed

* The cumulocity-pyton-api library is now available on [PyPI](https://pypi.org) under the name `c8y_api` (see https://pypi.org/project/c8y-api/) 
* Updated README to reflect installation from PyPI 


## Version 1.0

Major refactoring of beta version:
* Unified user experience
* Complete documentation
* Performance improvements
* Introduced `CumulocityApp` to avoid mix-up with `CumulocityApi`
* Complete unit tests
* Structured integration tests
* Removed samples (sorry, need to be re-organized)
