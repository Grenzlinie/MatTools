from __future__ import annotations

import os

import pytest

from pymatgen.core import SETTINGS

module_dir = os.path.dirname(__file__)


@pytest.fixture(autouse=True)
def _set_aims_species_dir_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIMS_SPECIES_DIR", f"{module_dir}/species_directory")


@pytest.fixture(autouse=True)
def _set_aims_species_dir_settings(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setitem(SETTINGS, "AIMS_SPECIES_DIR", f"{module_dir}/species_directory")
