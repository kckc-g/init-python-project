#!/usr/bin/env python3
from __future__ import print_function

import argparse
import logging
import os
import subprocess
import sys
import tempfile

CURRENT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
CURRENT_PYTHON = os.path.realpath(os.path.abspath(sys.executable))

ENV_SH = os.path.join(CURRENT_DIR, 'env.sh')

VENV_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..', '.venv'))

def create_env_file():
    """Create the default env.sh if not exist"""

    path = os.path.join(CURRENT_DIR, 'env.sh')

    # Only create if does not exist already
    if os.path.exists(path):
        return

    with open(path, 'w') as f:
        f.write("""
#!/bin/bash

PROJECT_DIR=$(realpath $(dirname $BASH_SOURCE)/..)

# Location of venv directory
VENV_DIR=${PROJECT_DIR}/.venv

# Run bootstrap.py to create the virtualenv environment
if ! [ -d "${VENV_DIR}" ]; then
    echo "No venv directory found, please run bootstrap.py to create the venv environment, exiting..."
    exit 1
fi

# Activate virtualenv if not already
if [ -z "${VIRTUAL_ENV}" ];
then
    echo "No active virtualenv found, activating from: '${VENV_DIR}'"
    . ${VENV_DIR}/bin/activate
fi

# Include src dir as well
export PYTHONPATH=${PROJECT_DIR}/src
""".strip())


def create_python_wrapper():
    """Create the default python wrapper: python.sh if not exist"""

    path = os.path.join(CURRENT_DIR, 'python.sh')

    # Only create if does not exist already
    if os.path.exists(path):
        return

    with open(path, 'w') as f:
        f.write("""
#!/bin/bash

# Disable core dump (no more core dump files)
ulimit -c 0

ENV_SH=$(dirname $BASH_SOURCE)/env.sh

if ! [ -f ${ENV_SH} ];
then
    echo "Missing env.sh file exiting ..."
    exit 1
fi

. ${ENV_SH}

PYTHON=${VIRTUAL_ENV}/bin/python

echo ${PYTHON}

exec ${PYTHON} "$@"
""".strip())

    os.chmod(path, 0o755)


def run_shell_command(commands, source_sh=None, stdout=None, shell='/bin/bash'):
    fd, path = tempfile.mkstemp(suffix='.sh')

    with os.fdopen(fd, 'w') as f:
        if shell:
            f.write('#!')
            f.write(shell)
            f.write('\n')

        if source_sh:
            f.write('source ')
            f.write(source_sh)
            f.write('\n')

        for c in commands:
            f.write(c)
            f.write(' ')

        f.write('\n')

    with open(path) as f:
        script_content = f.read()
        logging.info('Executing script:\n"""\n{}"""'.format(script_content))

    try:
        os.chmod(path, 0o755)

        p = subprocess.Popen([path], stdout=stdout)
        output, _ = p.communicate()

        # If return code is not 0
        if p.returncode:
            print(output)
            raise subprocess.CalledProcessError(p.returncode, script_content)

        if output is not None:
            return [l for l in output.splitlines()]
    finally:
        os.unlink(path)

def setup_venv(virtualenv_path, python_path):
    py_dir = os.path.dirname(python_path)

    # Search virtualenv path:
    paths = [
        # First we check specified virtualenv
        virtualenv_path,
        # Then we check if specified python executable comes with virtualenv
        os.path.join(os.path.dirname(python_path), 'virtualenv'),
        # Then we check current python used to run this script has virtualenv
        os.path.join(sys.exec_prefix, 'bin', 'virtualenv'),
    ]

    # Default to virtualenv available in PATH
    virtualenv = 'virtualenv'

    for p in paths:
        if p and os.path.exists(p):
            virtualenv = p
            break

    logging.info('Setting up venv directory at: "%s"', VENV_DIR)

    commands = [
        virtualenv,
        '--python={}'.format(python_path),
        '--never-download',
        VENV_DIR
    ]

    run_shell_command(commands=commands)


def pip_install(pip_index_url='https://pypi.org/simple', pip_extra_index_url=None, requirements_files=[]):
    requirements_files = [requirements_files] if isinstance(requirements_files, str) else requirements_files

    commands = [
        os.path.join(VENV_DIR, 'bin', 'pip'),
        'install',
        '--index-url={}'.format(pip_index_url),
        '--extra-index-url={}'.format(pip_extra_index_url or ''),
        '--timeout=120'
    ]

    for req in requirements_files:
        if not os.path.exists(req):
            raise Exception("Requirement file: {} does not exists.".format(req))

        logging.info('Pip installing requirement file: "{}"'.format(req))

        run_shell_command(commands + ['--requirement={}'.format(req)], source_sh=ENV_SH)

def main():
    parser = argparse.ArgumentParser()

    # Args for override executable paths
    parser.add_argument('--python', default=CURRENT_PYTHON,
                        help='path to python executable used for virtualenv to create the environment, (default: {})'.format(CURRENT_PYTHON))

    parser.add_argument('--virtualenv-path',
                        help='path to virtualenv, if unspecified search in the same location as python executable')

    # Pypi URLs
    parser.add_argument('--pip-index-url',
                        default='https://pypi.org/simple',
                        help='URL for pypi repo, (default: https://pypi.org/simple)')

    parser.add_argument('--pip-extra-index-url',
                        default='',
                        help='extra URL for pypi repo, (default: None)')

    # Requirement files
    parser.add_argument('--requirements',
                        nargs='*',
                        default=[os.path.abspath(os.path.join(CURRENT_DIR, '..', 'requirements.txt'))],
                        help='path to requirements.txt file, can specify more than one, (default: requirements.txt)')

    # Logging level
    parser.add_argument('--logging-level',
                        default=logging.getLevelName(logging.INFO),
                        help='logging level')

    args = parser.parse_args()

    logging.basicConfig(level=logging.getLevelName(args.logging_level))

    # Create env.sh and python.sh if they don't exist
    create_env_file()
    create_python_wrapper()

    # Setup virtual env if not already
    if 'VIRTUAL_ENV' not in os.environ:
        setup_venv(virtualenv_path=args.virtualenv_path, python_path=args.python)

    # Install requirements
    pip_install(pip_index_url=args.pip_index_url,
                pip_extra_index_url=args.pip_extra_index_url,
                requirements_files=args.requirements)

if __name__ == '__main__':
    sys.exit(main())

