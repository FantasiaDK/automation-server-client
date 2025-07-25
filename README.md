# Automation Server Client

This is the automation server package that allows you to interface with the automation-server API.

## Installation

You can install the package using uv:

```bash
uv add "git+https://github.com/odense-rpa/automation-server-client.git"
```

## Usage
Here is a basic example of how to use the package:

```python
    # Set up configuration
    ats = AutomationServer.from_environment()    
    
    workqueue = ats.workqueue()   
```

For a more complete implementation see the [process-template](https://github.com/odense-rpa/process-template).

## Features

* Interface with the automation-server API
* Retrieve process and workqueue status
* Retrieve work items for processing
* Logging actions and workitems

## Documentation
For detailed documentation, please visit Documentation Link.

## Contributing
Contributions are welcome! Please read the contributing guidelines first.

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
If you have any questions or feedback, please contact us at tyra_rpa@odense.dk.

