## Installing from PyPi on Windows
Note that most of these instructions involve using virtual environments for Python packages. If you
don't care about those (or already have them installed and use them), you can skip down to the
*Install program locally* step.

### Install virtual environment tools for program
Pip itself is not exactly optional, you will need it to install Pillow from http://pypi.python.org, but
the virtualenv tool is not required. However, it's good practice to use it - it allows you keep
Python packages in isolated environments.

    http://www.tylerbutler.com/2012/05/how-to-install-python-pip-and-virtualenv-on-windows-with-powershell/
    http://stackoverflow.com/questions/10635/why-are-my-powershell-scripts-not-running

If you don't install virtualenv, the only thing that will work differently - when you do `pip install pillow`,
it will install package `pillow` globally, rather than in a self-contained virtual environment.

### Powershell
Run Powershell, then you can do these commands:

    Import-Module virtualenvwrapper
    mkvirtualenv psp_stuff

Once you've created the virtual environment, the next time you start Powershell:

    Import-Module virtualenvwrapper
    workon psp_stuff

It's possible to create a Powershell profile that does all of this, automatically.

#### Edit Powershell Profile
Every time you start up Powershell, you need certain variables set. You can either do that manually, each time, ex:

    Import-Module virtualenvwrapper
    workon psp_stuff
    $env:PYTHONPATH += ";C:\venvs\psp_stuff\lib\site-packages";  # Wherever you keep your virtualenvs

Or you can edit a Profile to contain those commands. There are several profile locations, but one example is:

    C:\Users\<yourname>\Documents\WindowsPowerShell\profile.ps1

### Install program locally
Once you're running Powershell, and optionally a virtual environment, installation with pip is simple:

    pip install psp_scan

### Run program in Windows

Currently the only method is to run as listed below, giving a _module_ path in a
command to Python. (I don't list all that in the docs below, however.):

#### start Powershell - if you didn't setup a Profile (above), then type:

    Import-Module virtualenvwrapper
    workon psp_stuff
    $env:PYTHONPATH += ";C:\venvs\psp_stuff\lib\site-packages";  # Wherever you keep your virtualenvs

#### test the installation:

    python -m psp_scan -h
      or
    python -m psp_scan pics\ship.pspimage -v

If everything is installed correctly, you should either see help, if you did `-h`, or:

    converting: .\pics\ship.pspimage                => C:\repo_dir\psp_scan\ship.png

## API Installation for Alpha Testers
After doing all the CLI steps to install the package, you should be able to do:

    $> python
    >>> from psp_scan import PSPImage
