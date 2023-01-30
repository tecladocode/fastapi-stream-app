import os
import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException, status
import b2sdk.v2 as b2
from dotenv import load_dotenv

load_dotenv()

info = b2.InMemoryAccountInfo()
b2_api = b2.B2Api(info)

application_key_id = os.getenv("B2_KEY_ID")
application_key = os.getenv("B2_APPLICATION_KEY")

b2_api.authorize_account("production", application_key_id, application_key)
bucket = b2_api.get_bucket_by_name("teclado-fastapi-stream")

router = APIRouter()

CHUNK_SIZE = 1024 * 1024

@router.post("/upload/")
async def upload_file(file: UploadFile):
    try:
        filepath = os.path.join('./', os.path.basename(file.filename))
        async with aiofiles.open(filepath, 'wb') as f:
            while chunk := await file.read(CHUNK_SIZE):
                await f.write(chunk)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail='There was an error uploading the file')
    finally:
        await file.close()
    

    uploaded_file = bucket.upload_local_file(
        local_file=filepath,
        file_name=file.filename
    )
    
    return {"message": f"Successfuly uploaded {file.filename}", "file_url": b2_api.get_download_url_for_fileid(uploaded_file.id_)}