import os
import io
import platform
import asyncio
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor

import magic
import pytesseract
import numpy as np
from PIL import Image
from PyPDF2 import PdfReader
from transformers import pipeline
from fuzzywuzzy import fuzz

# Initialize components
mime_checker = magic.Magic(mime=True)
executor = ThreadPoolExecutor(max_workers=4)

# Load classification model
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

# Categories and keywords
labels = ["drivers_licence", "bank_statement", "invoice", "unknown"]
match_terms = {
    'drivers_licence': ['license', 'id card', 'identification'],
    'bank_statement': ['bank', 'statement', 'account history'],
    'invoice': ['invoice', 'receipt', 'bill']
}

# Minimum confidence scores
fuzzy_match_score = 90
zero_shot_score = 0.9

def read_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def read_image(data: bytes) -> str:
    img = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(img)

# Supported file types
handlers = {
    'application/pdf': read_pdf,
    'image/jpeg': read_image,
    'image/png': read_image
}

def extract_text(data: bytes, mime_type: str) -> str:
    handler = handlers.get(mime_type)
    if not handler:
        return ""
    return handler(data)

def fuzzy_match(text: str) -> Tuple[str, float]:
    best_category, best_score = 'unknown', 0
    for category, terms in match_terms.items():
        for term in terms:
            score = fuzz.partial_ratio(text.lower(), term.lower())
            if score > best_score:
                best_category, best_score = category, score
    return best_category, best_score / 100.0

def zero_shot_classify(text: str) -> Tuple[str, float]:
    result = classifier(text, candidate_labels=labels)
    label, score = result['labels'][0], result['scores'][0]
    return (label, score) if score >= zero_shot_score else ('unknown', score)

def classify_file(file_data: bytes, filename: str) -> dict:
    # Get file type
    mime_type = mime_checker.from_buffer(file_data)

    # Try file name match
    name_guess, name_score = fuzzy_match(filename)
    if name_score >= fuzzy_match_score / 100:
        return {'category': name_guess, 'confidence': name_score, 'method': 'filename'}

    # If file name match isn't found, extract text and match file content
    extracted_text = extract_text(file_data, mime_type)
    if not extracted_text.strip():
        return {'category': 'unknown', 'confidence': 0.0, 'method': 'no_text'}
    
    content_guess, content_score = fuzzy_match(extracted_text)
    if content_score >= fuzzy_match_score / 100:
        return {'category': content_guess, 'confidence': content_score, 'method': 'content'}

    # If file content match isn't found, use zero shot classifier
    model_guess, model_score = zero_shot_classify(extracted_text)
    return {'category': model_guess, 'confidence': model_score, 'method': 'model'}

async def classify_batch_files(files: List[Tuple[bytes, str]]) -> List[dict]:
    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(executor, classify_file, file_data, file_name)
        for file_data, file_name in files
    ]
    return await asyncio.gather(*tasks)

