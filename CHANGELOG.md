# Changelog

## Version 1.4

* Fixed https://github.com/SoftwareAG/cumulocity-python-api/issues/25
  The SimpleTenantApp did not include the tenant ID into the username which is not supported 
  by all Cumulocity instances.

* Adding class _QueryUtil, bundling query encoding related functionality.

* Added tests for special character parsing.

* Fixed handling and documentation of inventory API for querying by name. 
  Added query parameter for specification of custom queries.

* Reverted changes in ComplexObject - a ComplexObject is not a dictionary-like class, it only   
  supports some dictionary-like access functions. But, for instance, updating a ComplexObject
  is very different from updating a dictionary. Hence, it no longer inherits MutableMapping.

## Version 1.3.2

### Changed

* Obfuscated internal properties in _DictWrapper which blocked standard dictionary behavior. 
  Code cleanup.

* ComplexObject & _DictMapping now both inherit MutableMapping (Thanks Sam!).

* The base API now ignores trailing slashes gracefully.


## Version 1.3.1

### Changed

* Switched to version 2.4.0 of PyJWT as recommended by https://nvd.nist.gov/vuln/detail/CVE-2022-29217 


## Version 1.3

### Changed

* All objects with fragments can now be converted to Pandas Series (Thanks Sam!).

### Added 

* Added support for operations (Thanks Alex!).

* Added support for lastUpdated field in alarms and events.


## Version 1.2

### Changed

* Changed behavior of Events and Alarms API. Previously, an undefined event/alarm time was set to the current datetime 
  when invoking the `.create` function on the object. This was handy but inconsistent to the REST API behavior and
  therefore removed. Instead, the constructor can now be invoked with `time='now'` as a shorthand. The `time` field
  is never set to a default value automatically.

* Added `samples` folder to linting task.

* Added device agent registration sample (Thanks Nick!).


## Version 1.1.1

### Added

* Added Multi-Tenant sample script (`samples/multi_tenant_app.py`).

* Added task `build-ms` task and corresponding script files to generate Cumulocity microservices from sample scripts.

### Fixes

* Fixed authentication (username must include tenant ID) for subscribed tenants in multi-tenant scenarios. 

* Fixed pylint dependency in `requirements.txt`.

* Added `cachetools` to library dependencies in `setup.cfg`.


## Version 1.1

### Notes

* _Warning_, this release is a breaking change as it introduces an `auth` parameter to the API base classes,
  `CumulocityRestAPI` and `CumulocityAPI`. This parameter should be the new standard to use (instead of just
  username and password).

* _Warning_, this release replaces the 'all-purpose' class `CumulocityApp` with specialized versions for multi-tenant
  (`MultiTenantCumulocityApp`) and single tenant (`SimpleCumulocityApp`) environments.

### Added

* Added `_util.py` file to hold all cross-class auxiliary functionality.

* Added `_auth.py` file to hold all cross-class authentication functionality. Moved corresponding code from file
  `app.__init__.py` to the `AuthUtil` class.
 
* Added `_jwt.py` with `JWT` class which encapsulates JWT handling for the libraries purpose. This is _not_ a full
  JWT implementation. 

* Added `HTMLBearerAuth` class which encapsulates Cumulocity's JWT token-based authentication mechanism. 
 
* Added token-based authentication support. All API classes now can be initialized with an AuthBase parameter which
  would allow all kinds of authentication mechanisms. As of now, `HTTPbasicAuth` and `HTTPBearerAuth` is supported.

* Added caching with TTL/Max Size strategies to `MultiTenantCumulocityApp` and `SimpleCumulocityApp`.

* Added samples: `user_sessions.py` illustrating how user sessions can be obtained and `simple_tenant_app.py` 
  illustrating how the `SimpleCumulocityApp` class is used.

* Added requirements: `cachetools` (for caching), `inputtimeout` and `flask` (for samples).

### Changed

* Fixed file opening in `post_file` function in `_base_api.py` to avoid files already being closed when posting.

* Removed class `CumulocityApp` as it was too generic and hard to use. Replaces with classes `SimpleCumulocityApp`
  which behaves pretty much identical and `MultiTenantCumulocityApp` which behances more like a factory.


## Version 1.0.2

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
