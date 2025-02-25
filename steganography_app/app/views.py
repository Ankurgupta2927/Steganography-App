import os
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from PIL import Image
from django.utils.http import quote

# Directory for storing uploaded and processed images
MEDIA_DIR = "media/"
os.makedirs(MEDIA_DIR, exist_ok=True)

def home(request):
    return render(request, 'index.html')

# Encode a message into an image (now with auto-conversion to PNG)
def encode_message(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']
        message = request.POST['message']

        fs = FileSystemStorage(location=MEDIA_DIR)
        filename = fs.save(image.name, image)
        img_path = os.path.join(MEDIA_DIR, filename)

        # Convert image to PNG if not already in PNG format
        converted_img_path = convert_to_png(img_path)

        img = Image.open(converted_img_path)
        encoded_img_path = os.path.join(MEDIA_DIR, "encoded_" + os.path.basename(converted_img_path))
        encode_image(img, message, encoded_img_path)

        return render(request, 'encode.html', {
            'encoded_img_path': f'/media/encoded_{os.path.basename(converted_img_path)}',
            'download_url': f'/download/{quote(os.path.basename(encoded_img_path))}'
        })
    
    return render(request, 'encode.html')

# Function to convert uploaded image to PNG if needed
def convert_to_png(img_path):
    img = Image.open(img_path)
    if img.format != 'PNG':  # Convert only if not already PNG
        new_path = os.path.splitext(img_path)[0] + ".png"
        img.convert('RGB').save(new_path, 'PNG')  # Convert and save as PNG
        os.remove(img_path)  # Remove the original non-PNG file
        return new_path
    return img_path  # If already PNG, return original path

# Decode a hidden message from an image
def decode_message(request):
    if request.method == 'POST' and request.FILES['image']:
        image = request.FILES['image']

        fs = FileSystemStorage(location=MEDIA_DIR)
        filename = fs.save(image.name, image)
        img_path = os.path.join(MEDIA_DIR, filename)

        img = Image.open(img_path)
        message = decode_image(img)

        return render(request, 'decode.html', {'message': message})
    
    return render(request, 'decode.html')

# Function to encode a message using LSB (Least Significant Bit) in the Red channel
def encode_image(img, message, output_path):
    img = img.convert('RGB')
    pixels = list(img.getdata())

    # Append a delimiter to indicate the end of the message
    message += "@@@"
    binary_msg = ''.join(format(ord(i), '08b') for i in message)
    
    # Check if the message is too long for the image
    if len(binary_msg) > len(pixels):
        raise ValueError("Message is too long to encode in the image.")

    new_pixels = []
    binary_index = 0

    for pixel in pixels:
        new_pixel = list(pixel)
        if binary_index < len(binary_msg):
            new_pixel[0] = (new_pixel[0] & ~1) | int(binary_msg[binary_index])  # Modify Red channel LSB
            binary_index += 1
        new_pixels.append(tuple(new_pixel))

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path)

# Function to decode the hidden message from an image
def decode_image(img):
    pixels = list(img.getdata())
    
    # Extract LSB from the Red channel
    binary_msg = "".join(str(pixel[0] & 1) for pixel in pixels)

    message = ""
    for i in range(0, len(binary_msg), 8):
        byte = binary_msg[i:i+8]
        if len(byte) < 8:
            break  # Avoid decoding an incomplete byte
        char = chr(int(byte, 2))
        message += char

        # Stop decoding once we hit the delimiter '@@@'
        if message.endswith('@@@'):
            return message[:-3]  # Remove the delimiter and return the message

    return message  # Return full message if delimiter is not found

# Function to allow users to download the encoded image
def download_image(request, filename):
    file_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/force-download')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponse("File not found", status=404)
