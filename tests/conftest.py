import pytest

from investopt.demo import demo
from investopt.generator import generate
from investopt.warehouse import build


@pytest.fixture(scope="session")
def dataset(tmp_path_factory):
    root = tmp_path_factory.mktemp("pipeline")
    generate(seed=42, leads=1500, root=root)
    return root


@pytest.fixture(scope="session")
def warehouse(dataset):
    build(dataset)
    return dataset


@pytest.fixture(scope="session")
def completed(tmp_path_factory):
    root = tmp_path_factory.mktemp("complete")
    demo(43, 1500, root)
    return root
