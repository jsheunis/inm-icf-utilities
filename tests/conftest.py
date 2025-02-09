from datalad.conftest import setup_package

# fixture setup
from datalad_next.tests.fixtures import (
    # no test can leave global config modifications behind
    check_gitconfig_global,
    # no test can leave secrets behind
    check_plaintext_keyring,
    # function-scope credential manager
    credman,
    # function-scope config manager
    datalad_cfg,
    # function-scope temporary keyring
    tmp_keyring,
    # function-scope, Dataset instance
    dataset,
    #function-scope, Dataset instance with underlying repository
    existing_dataset,
    #function-scope, Dataset instance with underlying Git-only repository
    existing_noannex_dataset,
)

from .fixtures import (
    data_webserver,
    dataaccess_credential,
)
