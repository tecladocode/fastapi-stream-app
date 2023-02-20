import os

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status

from libs.b2 import b2_upload_file

router = APIRouter()

CHUNK_SIZE = 1024 * 1024


@router.post("/upload")
async def upload_file(file: UploadFile):
    try:
        filepath = os.path.join("./", os.path.basename(file.filename))
        async with aiofiles.open(filepath, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                await f.write(chunk)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )
    finally:
        await file.close()

    file_url = b2_upload_file(local_file=filepath, file_name=file.filename)

    return {"detail": f"Successfuly uploaded {file.filename}", "file_url": file_url}
