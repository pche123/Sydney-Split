"""Fast checks of the line-test library on a toy city: a 10 x 10 grid of 1 km square areas."""
import numpy as np
import pytest
from scipy import sparse
from shapely.geometry import box

from linetests import (MultiScaleNull, LineTest, calibrated_map_test, step_test, two_type_line, logit_surface)

K = 10


@pytest.fixture(scope="module")
def city():
    geom = [box(c * 1000, r * 1000, (c + 1) * 1000, (r + 1) * 1000) for r in range(K) for c in range(K)]
    I, J = [], []
    for r in range(K):
        for c in range(K):
            i = r * K + c
            if c + 1 < K: I.append(i); J.append(i + 1)
            if r + 1 < K: I.append(i); J.append(i + K)
    W = np.full(len(I), 1000.0)
    return geom, np.array(I), np.array(J), W


@pytest.fixture(scope="module")
def null(city):
    geom, I, J, W = city
    return MultiScaleNull(geom, I, J, W, m=9)


def test_msr_rotation_keeps_band_energy_and_flattens_it(city):
    """Proposition 1: a random rotation keeps a band's total energy and spreads it evenly on average."""
    geom, I, J, W = city
    T = LineTest(K * K, I, J, W, seed=1)
    f = T.V[:, 0] * 3 + T.V[:, 5] * 0.5            # a smooth map: almost all energy in the first pattern
    coef = []
    for Rs in T.rotations(400):
        c = T.V.T @ T.rotate(f, Rs)
        coef.append(c[:12] ** 2)
    coef = np.array(coef)
    np.testing.assert_allclose(coef.sum(1), coef.sum(1)[0], rtol=1e-8)      # energy kept
    assert coef.mean(0).std() / coef.mean(0).mean() < 0.25                    # spread evenly on average


def test_landscape_fit_tells_broad_from_fine_maps(null):
    rng = np.random.default_rng(0)
    xy = np.array([[c, r] for r in range(K) for c in range(K)], float)
    broad = xy[:, 0] + 0.1 * rng.standard_normal(K * K)          # one gentle tilt across the city
    fine = rng.standard_normal(K * K)                            # no spatial pattern
    assert null.fit(broad)["ell"] > null.fit(fine)["ell"]
    assert null.fit(fine)["tau"] > null.fit(broad)["tau"]


def test_calibrated_map_test_returns_valid_p(null):
    rng = np.random.default_rng(1)
    f = null.simulate(null.fit(rng.standard_normal(K * K)), 1, rng)[:, 0]
    r = calibrated_map_test(null, f, B=49, R=5, Bin=19, seed=2)
    assert 0 < r["p_raw"] <= 1 and 0 < r["p_cal"] <= 1


def test_edge_test_finds_a_cliff_but_not_a_slope(null):
    xy = np.array([[c, r] for r in range(K) for c in range(K)], float)
    rng = np.random.default_rng(3)
    slope = xy[:, 0] / K + 0.2 * rng.standard_normal(K * K)
    cliff = (xy[:, 0] >= K / 2) * 3.0 + 0.2 * rng.standard_normal(K * K)
    assert step_test(null, cliff, B=99, seed=4)[0] < 0.05
    assert step_test(null, slope, B=99, seed=4)[0] > 0.05


def test_empty_areas_carry_no_information():
    area = np.array([0, 0, 0, 1, 1])                  # area 2 has no records at all
    y = np.array([1, 0, 1, 0, 0], float)
    s, v = logit_surface(area, y, 3)
    assert v[2] == pytest.approx(4.0)                 # 1/0.5 + 1/0.5: says almost nothing
    assert v[0] < v[2] and s[0] > s[1]


def test_record_line_rebuilds_its_own_map():
    # 3 areas, 6 venues; each area counts its own venues
    area = np.array([0, 0, 1, 1, 2, 2]); y = np.array([1, 1, 1, 0, 0, 0], float)
    M = sparse.csr_matrix((np.ones(6), (area, np.arange(6))), shape=(3, 6))
    L = two_type_line("toy", area, M, y, lambda a, b: a / (a + b), 3)
    np.testing.assert_allclose(L.field, [1.0, 0.5, 0.0])
    sim = L.simulate([np.array([10.0, 0.0, -10.0])], np.random.default_rng(0))
    assert sim[:2].all() and not sim[4:].any()
