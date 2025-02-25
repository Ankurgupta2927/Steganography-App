# Steganography App

This is a Django web application that allows users to encode and decode hidden messages within images using the Least Significant Bit (LSB) method. The application also supports automatic conversion of uploaded images to PNG format for consistent encoding.

## Features

- **Encode Message**: Hide a secret message within an image using LSB encoding (Least Significant Bit) in the Red channel of the image.
- **Decode Message**: Extract hidden messages from an image that was previously encoded.
- **Automatic PNG Conversion**: Automatically converts uploaded images to PNG format if they are not already in PNG.
- **Download Encoded Image**: Users can download the image after the message is encoded.

## Requirements

- Python 3.x
- Django
- Pillow (Python Imaging Library)

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/Ankurgupta2927/Steganography-App.git
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Django's migrations to set up the database:
   ```bash
   python manage.py migrate
   ```
4. Start the development server:
   ```bash
   python manage.py runserver
   ```
5. Access the app at http://localhost:8000.

## Usage
1. Home Page:
A simple welcome page that navigates to either encoding or decoding options.
![image](https://github.com/user-attachments/assets/2c6124a4-9c59-48f0-808f-80e0edc0bc23)

2. Encode Message:
Upload an image (JPG, PNG, etc.) and provide a message to encode.
The image is automatically converted to PNG if needed, and the message is encoded using the LSB method.
The encoded image is made available for download.
![image](https://github.com/user-attachments/assets/dafbb446-4df2-494e-bc90-787dfd414215)

![image](https://github.com/user-attachments/assets/eccf2e66-9931-4c69-a441-1b0f9a7628ac)

Decode Message:
Upload an encoded image (PNG format).
The hidden message is decoded and displayed.
![image](https://github.com/user-attachments/assets/7214d026-cf5d-44a0-9365-553231015813)
![image](https://github.com/user-attachments/assets/b203e638-db8b-4ff2-8e6b-3223345ebdbf)


