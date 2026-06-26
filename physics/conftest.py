import pytest, pathlib, pinocchio as pin

@pytest.fixture
def so101_model():
    path = pathlib.Path(__file__).parents[1] / "models/so101/so101_new_calib.urdf"
    return pin.buildModelFromUrdf(path)