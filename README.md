STAR-Discovery
===

Usage
---

    usage: STAR Discovery [-h] [-v] {html,info,read} ...

    Simulates the STAR-Discovery algorithm on plaintext HTML

    positional arguments:
    {html,info,read}
        html            generate HTML based on the recovered portion of each input
                        document
        info            query information about documents from a star-discovery
                        database
        read            read input HTML files into a star-discovery database

    options:
    -h, --help        show this help message and exit
    -v, --version     show program's version number and exit

Installation
---

    # For standard installation
    pip install -e .

    # Or for development
    pip install -e '.[dev]'

    # After which you should have a `star-discovery` executable in your path.
    which star-discovery && echo "successfully installed"
