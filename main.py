from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from io import BytesIO
from dotenv import load_dotenv
import os
import re
import Levenshtein
from PIL import Image
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine, SessionLocal
import uvicorn

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# CORS settings
origins = [
    "http://localhost",
    "http://localhost:8000",
    "*"
    # Add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Define Pydantic models
class StudentBase(BaseModel):
    course_name: str
    course_fee: str
    student_name: str
    student_father_name: str
    student_mother_name: str
    gender: str
    day: str
    month: str
    year: str
    category: str
    occupation: str
    organization_name: str
    school_college_name: str
    others_detail: str
    student_phone: str
    student_mobile: str
    email: str
    address: str
    village: str
    block: str
    sub_division: str
    district: str
    state: str
    pincode: str

class UserBase(BaseModel):
    username: str

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/user/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: Session = Depends(get_db)):
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/student/", status_code=status.HTTP_201_CREATED)
async def create_student(student: StudentBase, db: Session = Depends(get_db)):
    db_student = models.Student(**student.dict())
    db.add(db_student)
    db.commit()
    return {"message": "Student information submitted successfully"}

# Azure Document Intelligence (Form Recognizer) configuration
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_KEY")

# Create an instance of DocumentAnalysisClient
document_intelligence_client = DocumentAnalysisClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

# A4 size in pixels at 150 DPI
A4_WIDTH_PIXELS = 1240
A4_HEIGHT_PIXELS = 1754



@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Validate the file format
        if file.content_type not in ["image/jpeg", "image/png", "image/tiff"]:
            raise HTTPException(status_code=400, detail="Invalid file format")

        # Read the uploaded file
        file_content = await file.read()

        # Open the image using Pillow
        image = Image.open(BytesIO(file_content))

        # Convert RGBA to RGB if necessary
        if image.mode == 'RGBA':
            image = image.convert('RGB')

        # Resize the image to fit within A4 dimensions while maintaining aspect ratio
        image.thumbnail((A4_WIDTH_PIXELS, A4_HEIGHT_PIXELS))

        # Convert to JPEG to apply compression and reduce file size
        compressed_image_stream = BytesIO()
        image.save(compressed_image_stream, format="JPEG", quality=85)
        compressed_image_stream.seek(0)

        model_id = "testmodel2"  # Replace with your custom model ID
        poller = document_intelligence_client.begin_analyze_document(
            model_id=model_id,
            document=compressed_image_stream
        )
        result = poller.result()

        # # Extract key-value pairs
        # key_value_pairs = {}
        # kv_pairs = list(result.key_value_pairs)  # Convert to list to access by index
        # for kv_pair in kv_pairs[3:]:  # Skip the first two pairs
        #     if kv_pair.key and kv_pair.value:
        #         processed_key = preprocess_key(kv_pair.key.content)
        #         closest_key = find_closest_key(processed_key, key_value_pairs.keys())
        #         if closest_key:
        #             key_value_pairs[closest_key] = kv_pair.value.content
        #         else:
        #             key_value_pairs[processed_key] = kv_pair.value.content

        # # Return the key-value pairs in the response
        # print(key_value_pairs)
        # return {"key_value_pairs": key_value_pairs}

        # Initialize a dictionary to hold field values
        field_values = {}

        # Analyze the result and extract field values
        for idx, document in enumerate(result.documents):
            print("--------Analyzing document #{}--------".format(idx + 1))
            print("Document has type {}".format(document.doc_type))
            print("Document has confidence {}".format(document.confidence))
            print("Document was analyzed by model with ID {}".format(result.model_id))
            for name, field in document.fields.items():
                field_value = field.value if field.value else field.content
                print("......found field of type '{}' with value '{}' and with confidence {}".format(field.value_type, field_value, field.confidence))
                field_values[name] = field_value  # Add the field value to the dictionary

        # Return the extracted field values in the response
        return {"field_values": field_values}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
def preprocess_key(key):
    # Remove numbers and special characters
    return re.sub(r"\d+\.?\s?", "", key).strip()

def find_closest_key(input_key, template_keys):
    closest_key = None
    closest_distance = float("inf")
    preprocessed_input_key = preprocess_key(input_key)
    for template_key in template_keys:
        preprocessed_template_key = preprocess_key(template_key)
        distance = Levenshtein.distance(
            preprocessed_input_key, preprocessed_template_key
        )
        if (
            distance < closest_distance
            and distance
            / max(len(preprocessed_input_key), len(preprocessed_template_key))
            < 0.2
        ):
            closest_distance = distance
            closest_key = template_key
    return closest_key

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
