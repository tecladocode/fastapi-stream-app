import contextlib
import pathlib

import pytest
from httpx import AsyncClient


# Add a sample image to the fake filesystem
@pytest.fixture()
def sample_image(fs) -> pathlib.Path:
    path = (pathlib.Path(__file__).parent / "assets" / "myfile.png").resolve()
    fs.add_real_directory(path)
    return path


# Mock the b2_upload_file function so that it returns a fake URL
@pytest.fixture(autouse=True)
def mock_b2_upload_file(mocker):
    return mocker.patch(
        "storeapi.routers.upload.b2_upload_file", return_value="https://fakeurl.com"
    )


# Mock the aiofiles.open function so that it
# returns a fake file object from the fake filesystem
@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker, fs):
    import io

    mock_open = mocker.patch("aiofiles.open")

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = "r"):
        out_fs_mock = mocker.AsyncMock(name=f"async_file_open:{fname!r}/{mode!r}")
        with io.open(fname, mode) as fin:
            out_fs_mock.read.side_effect = fin.read
            yield out_fs_mock

    mock_open.side_effect = async_file_open
    return mock_open


@pytest.mark.anyio
async def test_upload_image(
    async_client: AsyncClient, logged_in_token: str, sample_image: pathlib.Path
):
    response = await async_client.post(
        "/upload",
        files={"file": open(sample_image, "rb")},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert response.status_code == 200
    assert response.json()["file_url"] == "https://fakeurl.com"
