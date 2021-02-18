# cumulocity-python-api

This project is a Python client for the Cumulocity REST API to make it easier to develop programs, scripts, device agents or microservices in Python.

## Installation

### Prerequisites

Before installing the module (or any module for that matter) consider creating
a virtual environment for your project. This is generally preferred over 
installing modules and dependencies globally:

```shell
cd <project-root>
python3 -m venv venv
source venv/bin/activate
``` 

### Installation using pip

The module is released as standard Python wheel (_.whl_ file). It can be
installed using pip using the following command:

```
pip install <release wheel file>
```

This will install all necessary dependencies automatically.  For your
references, the module's dependencies are also listed in file _requirements.txt_.
 
### Manual installation

The module sources can be used directly within your Python 3 project. Simply
copy the _c8y_api_ folder to your sources root and install the requirements by
running the following command. The _requirements.txt_ file is part of the sources.

```
pip3 install -r requirements.txt
```

If the _c8y_api_ folder is in your sources root folder all imports should
work right away. Alternatively you can add _c8y_api_ to your _PYHTONPATH_:

```
export PYTHONPATH=<project-root>/c8y_api; $PYTHONPATH
```

## Licensing

This project is licensed under the Apache 2.0 license - see <https://www.apache.org/licenses/LICENSE-2.0>

______________________
These tools are provided as-is and without warranty or support. They do not constitute part of the Software AG product suite. Users are free to use, fork and modify them, subject to the license agreement. While Software AG welcomes contributions, we cannot guarantee to include every contribution in the master project.

______________________
For more information you can Ask a Question in the [TECHcommunity Forums](http://tech.forums.softwareag.com/techjforum/forums/list.page?product=cumulocity).

You can find additional information in the [Software AG TECHcommunity](http://techcommunity.softwareag.com/home/-/product/name/cumulocity).

Contact us at [TECHcommunity](mailto:technologycommunity@softwareag.com?subject=Github/SoftwareAG) if you have any questions.

