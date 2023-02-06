from functools import lru_cache
import b2sdk.v2 as b2
from config import config


@lru_cache()
def b2_api():
    info = b2.InMemoryAccountInfo()
    b2_api = b2.B2Api(info)

    b2_api.authorize_account("production", config.B2_KEY_ID, config.B2_APPLICATION_KEY)
    return b2_api


@lru_cache()
def b2_get_bucket(api: b2.B2Api):
    return api.get_bucket_by_name(config.B2_BUCKET_NAME)


def b2_upload_file(local_file: str, file_name: str):
    api = b2_api()
    uploaded_file = b2_get_bucket(api).upload_local_file(
        local_file=local_file, file_name=file_name
    )
    return api.get_download_url_for_fileid(uploaded_file.id_)
