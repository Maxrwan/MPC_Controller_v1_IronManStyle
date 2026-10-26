"""L3-only fixtures. Root tests/conftest.py must be excluded with --confcutdir."""

import json
import os
from pathlib import Path

import pytest


@pytest.fixture
def literal():
    return json.loads((Path(__file__).parent / "fixtures/literal_oracles.json").read_text())


@pytest.fixture
def parameters(literal):
    from ct1.contracts import FrozenParameters

    return FrozenParameters(literal["synthetic_parameters"], "a" * 64)


@pytest.fixture
def point():
    from ct1.contracts import CurvaturePolicy, OperatingTuple, TupleRole

    return OperatingTuple(
        "TOY:actual",
        "TOY",
        TupleRole.ACTUAL_HELD,
        (2.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0),
        1.0,
        0,
        0,
        CurvaturePolicy.FROZEN_EXOGENOUS,
    )


@pytest.fixture
def jet():
    from ct1.contracts import BranchSpec, GeometryJet, QualificationStatus

    return GeometryJet(
        1.0,
        1.0,
        1.0,
        0,
        0.0,
        0.0,
        ((1.0, 0.0), (0.0, 0.0), (0.0, 0.0)),
        BranchSpec(),
        QualificationStatus.QUALIFIED,
    )


@pytest.fixture
def pair_factory():
    import numpy as np
    from ct1.contracts import CurvaturePolicy, EvaluationKey, MapId, SubsystemPair

    def build(a, b, continuous=False):
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        key = EvaluationKey(
            "TOY",
            "TOY",
            MapId.C_FIXED if continuous else MapId.D_TRACKER,
            CurvaturePolicy.FROZEN_EXOGENOUS,
            "a" * 64,
            0,
        )
        return SubsystemPair(
            key,
            "full",
            a,
            b,
            tuple("x" + str(i) for i in range(len(a))),
            tuple("u" + str(i) for i in range(b.shape[1])),
        )

    return build


@pytest.fixture
def inputs():
    import subprocess

    from ct1.contracts import InputSpec
    from ct1.inputs import verify_inputs

    root = Path(__file__).resolve().parents[2]
    archive = Path(os.environ["CT1L_ARCHIVE_ROOT"])
    sha = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    return verify_inputs(InputSpec(root, archive, root / "docs/ct1/ct1l", sha)).unwrap()


@pytest.fixture
def bundle(inputs):
    from ct1.source_adapter import build_sources

    return build_sources(inputs).unwrap()
