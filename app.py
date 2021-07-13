import dicomweb_client
from fastapi import (
    FastAPI,
    File, UploadFile
)
from typing import List
from dicomweb import dicomweb_store_instance
import json
import pydicom
from dicomweb_client.api import DICOMwebClient

config = json.load(open('config.json'))

project_id = config['project']
location = 'us-central1'
dataset_id = config['healthcare_dataset_name']
dicom_store_id = config['dicom_store_name']
dcm_file = None

from dicomweb_client.session_utils import create_session_from_gcp_credentials

session = create_session_from_gcp_credentials()

dicom_client = DICOMwebClient(
    url="https://healthcare.googleapis.com/v1/projects/uccc-aisr/locations/us-central1/datasets/uccc-aisr-b67a21b/dicomStores/uccc-aisr-ba50ed5/dicomWeb",
    session=session
)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post('/files/')
async def store_files(files: List[UploadFile] = File(...)):
    contents = pydicom.dcmread(files[0].filename)
    res = dicom_client.store_instances(datasets = [contents])
    return res.to_json_dict()
