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

# a path to the script that starts or restarts container
RUN_CONTAINER_SCRIPT_PATH = INSTANCE_SCRIPTS_DIR + '/run_container.sh'

"""
CONTAINER FILE STRUCTURE
"""

# a base directory for temporary files inside the container
CONTAINER_TMP_DIR = '/tmp/spotty'

# a temporary directory for custom user scripts ("spotty run" command)
CONTAINER_RUN_SCRIPTS_DIR = CONTAINER_TMP_DIR + '/scripts/run'
