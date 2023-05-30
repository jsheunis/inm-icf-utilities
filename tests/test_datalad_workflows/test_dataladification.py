from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import (
    urlparse,
    urlunparse,
    ParseResult,
)

from datalad.api import clone
from datalad.distribution.dataset import Dataset
from datalad.runner.runner import WitlessRunner
from datalad.tests.utils_pytest import on_appveyor
from datalad_next.credman import CredentialManager

from .utils import get_restricted_realm


existing_visits = ['visit_a', 'visit_b']


def run_script(name: str,
               working_directory: str | Path,
               study_id: str,
               visit_id: str,
               ):

    script_path = Path(*(Path(__file__).parts[:-3] + ('bin',))) / name
    runner = WitlessRunner(cwd=working_directory, env=dict(os.environ))
    runner.run(
        (['sudo', '-E', '--preserve-env=PATH'] if on_appveyor else []) + [
            str(script_path),
            '--id',
            study_id,
            visit_id
        ]
    )


def dataladify_visits(studies_dir: Path,
                      studies: list[str],
                      visits: list[str]
                      ):
    for study in studies:
        for visit in visits:
            run_script(
                'dataladify_studyvisit',
                studies_dir,
                study, visit
            )


def get_clone_annex_url(source_url: str,
                        study: str,
                        visit: str
                        ) -> tuple[str, str]:

    if source_url.endswith('/'):
        source_url = source_url[:-1]

    access_url = f'{source_url}/{study}'
    auth_realm = get_restricted_realm(access_url)

    parsed_url = urlparse(access_url)

    copy_attributes = ['scheme', 'netloc', 'path', 'params', 'query', 'fragment']
    realm_parsed_url = ParseResult(**{
        name: getattr(parsed_url, name) if name != 'path' else auth_realm
        for name in copy_attributes
    })

    return (
        'datalad-annex::?type=external&externaltype=uncurl'
        f'&url={source_url}/{study}/{visit}_{{{{annex_key}}}}'
        '&encryption=none',
        urlunparse(realm_parsed_url),
    )


def add_credentials(realms: Iterable[str],
                    credentials: dict,
                    credman: CredentialManager,
                    ):

    # Add credentials for all URLs to credential manager
    for index, realm in enumerate(realms):
        kwargs = {
            **credentials,
            'name': f'icf-test-credentials-{index}',
            'realm': realm
        }
        result = credman.set(**kwargs)
        assert result is not None


def clone_visit(path: Path,
                source_url: str,
                study: str,
                visit: str,
                credentials: dict,
                credman: CredentialManager,
                ) -> Dataset:

    # Get involved URLs and set credentials for `auth_url`
    clone_url, auth_realm = get_clone_annex_url(source_url, study, visit)
    add_credentials([auth_realm], credentials, credman)

    # Clone a visit from the clone URL
    return clone(source=clone_url, path=path)


def test_dataladification(tmp_path: Path,
                          test_studies_dir: str,
                          test_study_names: list[str],
                          data_webserver: str,
                          dataaccess_credential: dict,
                          credman: CredentialManager,
                          ):

    # Perform dataladification
    dataladify_visits(
        Path(test_studies_dir),
        test_study_names,
        existing_visits,
    )

    # Try to clone the datasets and fetch the dicom tarfile
    for study in test_study_names:
        for visit in existing_visits:
            dataset = clone_visit(
                tmp_path / f'ds_{study}_{visit}',
                data_webserver,
                study,
                visit,
                dataaccess_credential,
                credman,
            )
            # Try to get the tar file and the DICOMs
            dataset.get(f'icf/{visit}_dicom.tar')
            dataset.get(f'{study}_{visit}')
