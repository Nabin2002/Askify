# Askify
# Question Answer Generator 

## Project Overview

This project allows you to generate question-answer pairs from a PDF file . It involves:
- Uploading a PDF file.
- Displaying the file content and generating QA pairs based on it.
- Provides download functionality for the generated QA pairs.

---

## Table of Contents
1. [Installation](#installation)
2. [Setup](#setup)
3. [Usage](#usage)
4. [Project Structure](#project-structure)
5. [Dependencies](#dependencies)

---

## Installation

Follow these steps to set up the project locally.

1. Clone the repository:
    ```bash
    git clone https://github.com/Nabin2002/Askify.git
    ```

2. Navigate into the project folder:
    ```bash
    cd Askify
    ```

3. Create a virtual environment:
    ```bash
    python -m venv myenv
    ```

4. Activate the virtual environment:
    - **On Windows**:
      ```bash
      myenv\Scripts\activate
      ```
    - **On Linux**:
      ```bash
      source myenv/bin/activate
      ```

5. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

---

## Setup

1. **Flask Backend**: Ensure you have the correct Flask routes set up to handle PDF file uploads and question generation.  
   The backend will process the uploaded PDF and generate questions and answer.

2. **Configure Mistral API**: If you're using Mistral’s model, ensure you’ve set up your API keys and the model is accessible.  
   You might need to modify some configurations in the backend to point to the correct API.

---

## Usage

### Starting the Application

1. **Run the Flask App**:
    ```bash
    python app.py
    ```

2. Open your browser and go to:  
   [http://127.0.0.1:5000](http://127.0.0.1:5000) (or wherever Flask is running).

### How to Use the Web Application

1. **Upload a PDF File**: Click on the "Upload your PDF file here" button to select your file.
2. **Generate QA Pairs**: After uploading, click on the "Generate QA Pair" button to process the PDF and generate questions.
3. **View & Download**: After the processing, you’ll be able to view the PDF content and download the generated question-answer pairs.

---


