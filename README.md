### Part 1: Enhancing the Classifier
1. Some simple improvements can be made to this classifier:
    -Extracting the text from files to have more data to find a match
    -Using fuzzy matching to cover misspellings/spelling differences (e.g. license/licence)
    -Using AI to identify document types
    -Including the method used and confidence score in the response for tracking metrics

2. A pipeline for classification can be used, falling back to the next method if the previous method fails:
    1. Fuzzy matching on the file name
    2. Use fuzzy matching on file content
    3. Use zero-shot classification on file content
    4. If all previous methods fail, return unknown

3. In order to extract text from files, PyPDF2 for pdfs and tesseract for image OCR are used. Further file types can easily be added later.

4. Zero-shot classification with pre-trained models allows for easily introducing new document types and scaling to new industries. I am using BART-large MNLI for this scenario, however other models may be more suitable in future (e.g. multilingual support)

### Part 2: Productionising the Classifier 
1. In order to handle larger volumes of documents, batch processing can be implemented to process multiple files in parallel

2. The app is containerised with Docker allowing for scaling up in production with Kubernetes

### Usage
1. Build and run using Docker Compose:
```bash
docker-compose up --build
```

2. Classify a single file:
```bash
curl -X POST -F 'file=@files/path_to_pdf.pdf' http://localhost:5000/classify_file
```

3. Classify multiple files in batches:
```bash
curl -X POST -F 'files[]=@files/path_to_pdf.pdf' -F 'files[]=@files/path_to_jpg.jpg' -F 'files[]=@files/path_to_png.png' http://localhost:5000/classify_batch_files
```

### Future Improvements
    -Adding testing
    -Using multiple classifiers instead of cascading may be more accurate (covering false positives such as misnamed files)
    -Implementing other document types such as excel sheets and docs