"""
INSTANCE FILE STRUCTURE
"""

# a base temporary directory on an instance
INSTANCE_SPOTTY_TMP_DIR = '/tmp/spotty'

# a base directory for instance-related files and directories
INSTANCE_DIR = INSTANCE_SPOTTY_TMP_DIR + '/instance'

# helper scripts
INSTANCE_SCRIPTS_DIR = INSTANCE_DIR + '/scripts'

# instance startup scripts
INSTANCE_STARTUP_SCRIPTS_DIR = INSTANCE_SCRIPTS_DIR + '/startup'

# a path to the script that attaches user to the container
CONTAINER_BASH_SCRIPT_PATH = INSTANCE_SCRIPTS_DIR + '/container_bash.sh'

# a base directory for Spotty logs
SPOTTY_LOGS_DIR = '/var/log/spotty'

# logs that are recorded with the "spotty run" command if the "-l" flag is specified
RUN_CMD_LOGS_DIR = SPOTTY_LOGS_DIR + '/run'

"""
CONTAINER FILE STRUCTURE
"""

# a base directory for temporary files inside the container
CONTAINER_TMP_DIR = '/tmp/spotty'

# Scripts that will be run inside the container. This directory is mapped to
# the HOST_CONTAINER_SCRIPTS_DIR directory on the host OS.
CONTAINER_SCRIPTS_DIR = CONTAINER_TMP_DIR + '/scripts'

# a temporary directory for custom user scripts ("spotty run" command)
CONTAINER_RUN_SCRIPTS_DIR = CONTAINER_SCRIPTS_DIR + '/run'
