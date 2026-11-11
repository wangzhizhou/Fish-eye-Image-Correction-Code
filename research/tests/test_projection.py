import numpy as np
import pytest
from fisheye_models import MODELS, focal_length, theta_to_p, p_to_theta, dp_dtheta


@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("fov", [np.pi / 3, np.pi / 2, 2.5, np.pi])
def test_focal_length_normalisation(model, fov):
    f = focal_length(model, 600.0, fov)
    assert abs(theta_to_p(model, fov / 2, f) - 600.0) < 1e-9


@pytest.mark.parametrize("model", MODELS)
def test_inverse(model):
    f = focal_length(model, 1.0, np.pi)
    th = np.linspace(0, np.pi / 2, 1001)
    assert np.max(np.abs(p_to_theta(model, theta_to_p(model, th, f), f) - th)) < 1e-7


@pytest.mark.parametrize("model", MODELS)
def test_monotone_on_hemisphere(model):
    f = focal_length(model, 1.0, np.pi)
    p = theta_to_p(model, np.linspace(0, np.pi / 2, 1000), f)
    assert np.all(np.diff(p) > 0)


def test_180deg_values():
    R = 1.0
    assert np.isclose(focal_length("STEREOGRAPHIC", R, np.pi), 0.5)
    assert np.isclose(focal_length("EQUIDISTANCE", R, np.pi), 2 / np.pi)
    assert np.isclose(focal_length("EQUISOLID", R, np.pi), 1 / np.sqrt(2))
    assert np.isclose(focal_length("ORTHOGONAL", R, np.pi), 1.0)
    # orthographic loses all radial resolution at 90 deg
    assert abs(dp_dtheta("ORTHOGONAL", np.pi / 2, 1.0)) < 1e-12


def test_fov_check():
    with pytest.raises(ValueError):
        focal_length("EQUIDISTANCE", 1, 0)
    with pytest.raises(ValueError):
        focal_length("EQUIDISTANCE", 1, 3.5)
