from fastapi import (
    FastAPI,
    File, UploadFile
)
from typing import List
from dicomweb import dicomweb_store_instance
import json

config = json.load(open('config.json'))

project_id = config['project']
location = 'us-central1'
dataset_id = config['healthcare_dataset_name']
dicom_store_id = config['dicom_store_name']
dcm_file = None


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/files/')
async def store_files(files: List[UploadFile] = File(...)):
    contents = await files[0].read()
    res = dicomweb_store_instance(project_id,location,dataset_id,dicom_store_id,contents)
    return res
