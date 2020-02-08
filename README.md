# init-python-project
Starting point for python project.

Sandboxes each project with it's own virtualenv

Simplest way:

```bash
# Clone this project, put into <folder_name>
git clone https://github.com/kckc-g/init-python-project.git <folder_name>

# Change into that directory
cd <folder_name>

# Remove .git history
rm -rf .git

# Remove this description
rm README.md
```

# USAGE

There is only one script here.

## Bootstrap

Bootstrapping is simple.

```bash
# While in the project folder
./bin/bootstrap.py
```

By default it installs packages specified in: requirements.txt with pip.

Requirements file maybe adjusted as:

```bash
# While in the project folder
./bin/bootstrap.py --requirements requirement.preliminary.txt requirements.txt requirements_2.txt
```

## Running Python Project Code
```bash
# Replace python with ./bin/python.sh
./bin/python.sh <follow by use python argument etc>
```

```bash
# Simply doing below runs the pyton interpreter 
./bin/python.sh
```
