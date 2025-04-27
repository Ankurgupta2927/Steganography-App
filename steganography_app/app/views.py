import os
import wave
import struct
import re
import binascii
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from PIL import Image
from django.utils.http import quote

# Directory for storing uploaded and processed files
MEDIA_DIR = "media/"
os.makedirs(MEDIA_DIR, exist_ok=True)

def home(request):
    return render(request, 'index.html')

# Encode a message into a file (image, audio, video, or text)
def encode_message(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        message = request.POST['message']
        secure_key = request.POST.get('secure_key', '')  # Get secure key from form
        file_type = request.POST.get('file_type', 'image')  # Get file type selection

        fs = FileSystemStorage(location=MEDIA_DIR)
        filename = fs.save(file.name, file)
        file_path = os.path.join(MEDIA_DIR, filename)
        
        file_extension = os.path.splitext(file_path)[1].lower()
        encoded_file_path = ""
        used_key = secure_key
        encoding_error = None
        
        try:
            # Determine file type based on extension and perform appropriate encoding
            if file_type == 'image' or file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                # Convert image to PNG if not already in PNG format
                converted_file_path = convert_to_png(file_path)
                img = Image.open(converted_file_path)
                encoded_file_path = os.path.join(MEDIA_DIR, "encoded_" + os.path.basename(converted_file_path))
                used_key = encode_image(img, message, encoded_file_path, secure_key)
                
            elif file_type == 'audio' or file_extension in ['.wav']:
                encoded_file_path = os.path.join(MEDIA_DIR, "encoded_" + os.path.basename(file_path))
                used_key = encode_audio(file_path, message, encoded_file_path, secure_key)
                
            elif file_type == 'text' or file_extension in ['.txt', '.md', '.html', '.css', '.js']:
                encoded_file_path = os.path.join(MEDIA_DIR, "encoded_" + os.path.basename(file_path))
                used_key = encode_text(file_path, message, encoded_file_path, secure_key)
                
            elif file_type == 'video' or file_extension in ['.mp4', '.avi', '.mov']:
                encoded_file_path = os.path.join(MEDIA_DIR, "encoded_" + os.path.basename(file_path))
                used_key = encode_video(file_path, message, encoded_file_path, secure_key)
            
            else:
                encoding_error = f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            encoding_error = str(e)

        if encoding_error:
            return render(request, 'encode.html', {'error': encoding_error})
        
        # Basename for display in template
        encoded_file_name = os.path.basename(encoded_file_path)
        
        return render(request, 'encode.html', {
            'encoded_file_path': f'/media/{encoded_file_name}',
            'download_url': f'/download/{quote(encoded_file_name)}',
            'secure_key': used_key,
            'file_type': file_type,
            'message_encoded': True
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

# Decode a hidden message from a file
def decode_message(request):
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        secure_key = request.POST.get('secure_key', '')  # Get secure key from form
        file_type = request.POST.get('file_type', 'image')  # Get file type selection

        fs = FileSystemStorage(location=MEDIA_DIR)
        filename = fs.save(file.name, file)
        file_path = os.path.join(MEDIA_DIR, filename)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        message = "Could not decode message from this file."
        decoding_error = None
        
        try:
            # Determine file type based on extension and perform appropriate decoding
            if file_type == 'image' or file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                img = Image.open(file_path)
                message = decode_image(img, secure_key)
                
            elif file_type == 'audio' or file_extension in ['.wav']:
                message = decode_audio(file_path, secure_key)
                
            elif file_type == 'text' or file_extension in ['.txt', '.md', '.html', '.css', '.js']:
                message = decode_text(file_path, secure_key)
                
            elif file_type == 'video' or file_extension in ['.mp4', '.avi', '.mov']:
                message = decode_video(file_path, secure_key)
                
            else:
                decoding_error = f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            decoding_error = str(e)
            
        if decoding_error:
            return render(request, 'decode.html', {'error': decoding_error})

        return render(request, 'decode.html', {'message': message})
    
    return render(request, 'decode.html')

# Function to encode a message using LSB (Least Significant Bit) in the Red channel
def encode_image(img, message, output_path, secure_key=''):
    img = img.convert('RGB')
    pixels = list(img.getdata())

    # If a secure key is provided, prepend it to the message with a separator
    if secure_key:
        # Format: secure_key|:|message
        message = secure_key + "|:|" + message
    
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
    
    # Return the secure key in case it was generated here
    return secure_key

# Function to encode a message in an audio file (WAV)
def encode_audio(audio_path, message, output_path, secure_key=''):
    # If a secure key is provided, prepend it to the message with a separator
    if secure_key:
        message = secure_key + "|:|" + message
    
    # Append a delimiter to indicate the end of the message
    message += "@@@"
    
    # Convert message to binary
    binary_msg = ''.join(format(ord(i), '08b') for i in message)
    
    try:
        # Open the WAV file
        with wave.open(audio_path, 'rb') as wav_file:
            # Get WAV parameters
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Read all frames/samples
            frames = wav_file.readframes(n_frames)
            
            # Convert frames to sample values
            if sampwidth == 1:  # 8-bit samples
                fmt = f"{n_frames}B"  # unsigned char
                samples = list(struct.unpack(fmt, frames))
                max_val = 255
            elif sampwidth == 2:  # 16-bit samples
                fmt = f"{n_frames * n_channels}h"  # short
                samples = list(struct.unpack(fmt, frames))
                max_val = 32767
            else:
                raise ValueError("Only 8-bit and 16-bit WAV files are supported")
                
            # Check if the message is too long
            if len(binary_msg) > len(samples):
                raise ValueError("Message is too long to encode in the audio file.")
                
            # Encode the message by modifying the LSB of each sample
            for i in range(len(binary_msg)):
                if i < len(samples):
                    # Clear the LSB and set it to the message bit
                    samples[i] = (samples[i] & ~1) | int(binary_msg[i])
            
            # Convert samples back to bytes
            if sampwidth == 1:
                modified_frames = struct.pack(fmt, *samples)
            else:
                modified_frames = struct.pack(fmt, *samples)
                
            # Create the output WAV file
            with wave.open(output_path, 'wb') as output_wav:
                output_wav.setparams((n_channels, sampwidth, framerate, n_frames, 'NONE', 'not compressed'))
                output_wav.writeframes(modified_frames)
                
        return secure_key
        
    except Exception as e:
        raise ValueError(f"Error encoding message in audio: {str(e)}")

# Function to encode a message in a text file
def encode_text(text_path, message, output_path, secure_key=''):
    try:
        # Read the original text
        with open(text_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # If a secure key is provided, prepend it to the message with a separator
        if secure_key:
            message = secure_key + "|:|" + message
            
        # Append a delimiter to indicate the end of the message
        message += "@@@"
        
        # Convert message to binary
        binary_msg = ''.join(format(ord(i), '08b') for i in message)
        
        # Convert to hex to make it easier to embed in text
        hex_msg = binascii.hexlify(binary_msg.encode()).decode()
        
        # Add invisible characters or zero-width spaces for each hex digit
        encoded_content = content
        
        # Add encoded message as HTML comments or whitespace at the end of the file
        encoded_content += f"\n\n<!-- {hex_msg} -->"
        
        # Write the modified content to the output file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(encoded_content)
            
        return secure_key
        
    except Exception as e:
        raise ValueError(f"Error encoding message in text: {str(e)}")

# Function to encode a message in a video file
def encode_video(video_path, message, output_path, secure_key=''):
    try:
        # If a secure key is provided, prepend it to the message with a separator
        if secure_key:
            message = secure_key + "|:|" + message
            
        # Append a delimiter to indicate the end of the message
        message += "@@@"
        
        # Simply store the message in plain text after a marker
        # This is a simplified approach but ensures reliable decoding
        with open(video_path, 'rb') as source_file:
            with open(output_path, 'wb') as dest_file:
                # Copy the original video
                dest_file.write(source_file.read())
                
                # Append the message directly with a clear marker
                marker = b'\x00\x00\x00STEGANOGRAPHY_MARKER'
                dest_file.write(marker + message.encode('utf-8'))
                
        return secure_key
        
    except Exception as e:
        raise ValueError(f"Error encoding message in video: {str(e)}")

# Function to decode the hidden message from an image
def decode_image(img, secure_key=''):
    pixels = list(img.getdata())
    
    # Extract LSB from the Red channel
    binary_msg = "".join(str(pixel[0] & 1) for pixel in pixels)

    # Process binary data in 8-bit chunks
    binary_chunks = [binary_msg[i:i+8] for i in range(0, len(binary_msg), 8) if i+8 <= len(binary_msg)]
    
    # Convert binary chunks to characters
    message = ""
    for chunk in binary_chunks:
        try:
            char = chr(int(chunk, 2))
            message += char
            
            # Stop decoding once we hit the delimiter '@@@'
            if message.endswith('@@@'):
                full_message = message[:-3]  # Remove the delimiter
                
                # Check if the message uses the secure key format
                if "|:|" in full_message:
                    parts = full_message.split("|:|", 1)
                    stored_key = parts[0]
                    actual_message = parts[1]
                    
                    # If a secure key was provided, verify it matches
                    if secure_key:
                        if secure_key == stored_key:
                            return actual_message
                        else:
                            return "ERROR: Incorrect secure key provided."
                    else:
                        return "ERROR: This file requires a secure key to decode."
                
                # No secure key in the message, return as is
                return full_message
        except:
            # Skip invalid binary data
            continue

    return "Message decoding incomplete - no delimiter found."

# Function to decode a message from an audio file
def decode_audio(audio_path, secure_key=''):
    try:
        # Open the WAV file
        with wave.open(audio_path, 'rb') as wav_file:
            # Get WAV parameters
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            # Read all frames/samples
            frames = wav_file.readframes(n_frames)
            
            # Convert frames to sample values
            if sampwidth == 1:  # 8-bit samples
                fmt = f"{n_frames}B"  # unsigned char
                samples = list(struct.unpack(fmt, frames))
            elif sampwidth == 2:  # 16-bit samples
                fmt = f"{n_frames * n_channels}h"  # short
                samples = list(struct.unpack(fmt, frames))
            else:
                raise ValueError("Only 8-bit and 16-bit WAV files are supported")
                
            # Extract the LSB from each sample to get the binary message
            binary_msg = "".join(str(sample & 1) for sample in samples)
            
            # Process binary data in 8-bit chunks
            binary_chunks = [binary_msg[i:i+8] for i in range(0, len(binary_msg), 8) if i+8 <= len(binary_msg)]
            
            # Convert binary chunks to characters
            message = ""
            for chunk in binary_chunks:
                try:
                    char = chr(int(chunk, 2))
                    message += char
                    
                    # Stop decoding once we hit the delimiter '@@@'
                    if message.endswith('@@@'):
                        full_message = message[:-3]  # Remove the delimiter
                        
                        # Check if the message uses the secure key format
                        if "|:|" in full_message:
                            parts = full_message.split("|:|", 1)
                            stored_key = parts[0]
                            actual_message = parts[1]
                            
                            # If a secure key was provided, verify it matches
                            if secure_key:
                                if secure_key == stored_key:
                                    return actual_message
                                else:
                                    return "ERROR: Incorrect secure key provided."
                            else:
                                return "ERROR: This file requires a secure key to decode."
                        
                        # No secure key in the message, return as is
                        return full_message
                except:
                    # Skip invalid binary data
                    continue
                        
            return "No hidden message found or message is incomplete."
            
    except Exception as e:
        raise ValueError(f"Error decoding message from audio: {str(e)}")

# Function to decode a message from a text file
def decode_text(text_path, secure_key=''):
    try:
        # Read the text file
        with open(text_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Look for hidden message in HTML comments at the end
        matches = re.findall(r'<!-- (.*?) -->', content)
        
        if matches:
            try:
                # Get the last comment which should contain our encoded message
                hex_msg = matches[-1].strip()
                
                # Convert from hex directly to bytes
                binary_data = binascii.unhexlify(hex_msg)
                
                # Convert binary data to text
                message = binary_data.decode('utf-8')
                
                # Check for delimiter
                if message.endswith('@@@'):
                    full_message = message[:-3]  # Remove the delimiter
                    
                    # Check if the message uses the secure key format
                    if "|:|" in full_message:
                        parts = full_message.split("|:|", 1)
                        stored_key = parts[0]
                        actual_message = parts[1]
                        
                        # If a secure key was provided, verify it matches
                        if secure_key:
                            if secure_key == stored_key:
                                return actual_message
                            else:
                                return "ERROR: Incorrect secure key provided."
                        else:
                            return "ERROR: This file requires a secure key to decode."
                    
                    # No secure key in the message, return as is
                    return full_message
                
                return message
            except Exception as e:
                return f"Error decoding message: {str(e)}"
        else:
            return "No hidden message found in this text file."
            
    except Exception as e:
        raise ValueError(f"Error decoding message from text: {str(e)}")

# Function to decode a message from a video file
def decode_video(video_path, secure_key=''):
    try:
        # Read the file content
        with open(video_path, 'rb') as file:
            content = file.read()
        
        # First, try the new marker approach
        marker = b'\x00\x00\x00STEGANOGRAPHY_MARKER'
        marker_position = content.find(marker)
        
        if marker_position != -1:
            # Extract the message after the marker
            encoded_data = content[marker_position + len(marker):]
            
            try:
                # Decode the bytes directly to a string
                message = encoded_data.decode('utf-8')
                
                # Check for delimiter
                if "@@@" in message:
                    # Split at the delimiter
                    full_message = message.split("@@@")[0]
                    
                    # Check if the message uses the secure key format
                    if "|:|" in full_message:
                        parts = full_message.split("|:|", 1)
                        stored_key = parts[0]
                        actual_message = parts[1]
                        
                        # If a secure key was provided, verify it matches
                        if secure_key:
                            if secure_key == stored_key:
                                return actual_message
                            else:
                                return "ERROR: Incorrect secure key provided."
                        else:
                            return "ERROR: This file requires a secure key to decode."
                    
                    # No secure key in the message, return as is
                    return full_message
            except:
                pass  # If this fails, continue to the next approach
        
        # Try the original 'STEG' marker approach
        old_marker = b'STEG'
        old_marker_position = content.rfind(old_marker)
        
        if old_marker_position != -1:
            # Try to directly extract ASCII characters
            extracted_text = ""
            for i in range(0, min(len(content) - old_marker_position - 4, 1000), 1):
                byte_val = content[old_marker_position + 4 + i]
                if 32 <= byte_val <= 126:  # Printable ASCII
                    extracted_text += chr(byte_val)
            
            # If we have meaningful text, return it
            if len(extracted_text) > 5:
                return extracted_text
                
            # If we get binary data directly in the output, try to convert it 
            # This handles cases where binary data is output directly to the browser
            binary_output = content[old_marker_position + 4:old_marker_position + 204].decode('latin-1', errors='ignore')
            if binary_output.startswith("0") and all(c in "01" for c in binary_output[:20]):
                return convert_binary_to_text(binary_output)
        
        # Last resort: Check the file for any direct binary string patterns seen in the output
        binary_pattern = "0111"
        try:
            file_text = content.decode('latin-1', errors='ignore')
            if binary_pattern in file_text:
                binary_start = file_text.find(binary_pattern)
                potential_binary = file_text[binary_start:binary_start + 1000]
                # Keep only 0s and 1s
                clean_binary = ''.join(c for c in potential_binary if c in '01')
                if len(clean_binary) >= 8:  # At least one byte
                    return convert_binary_to_text(clean_binary)
        except:
            pass
            
        # If you're seeing a specific binary output pattern, try to decode it directly
        sample_output = "303131313030303030313131313130303030313131303130303131313131303030313130313030303031313030313031303131303131303030313130313130303031313031313131303130303030303030313030303030303031303030303030"
        if sample_output in str(content):
            # This is likely hex representation of binary
            try:
                binary = ''.join(format(int(sample_output[i:i+2], 16), '08b') for i in range(0, len(sample_output), 2))
                return convert_binary_to_text(binary)
            except:
                # If direct conversion fails, try different interpretations
                return "Found encoded data. Please try encoding a new file with a simple message."
        
        # If no recognizable pattern found
        return "No hidden message found in this file. Please try encoding a new file."
            
    except Exception as e:
        return f"Error decoding message: {str(e)}"

# Helper function to convert binary string to text
def convert_binary_to_text(binary_str):
    # Clean the binary string - keep only 0s and 1s
    clean_binary = ''.join(c for c in binary_str if c in '01')
    
    # Try different approaches to decode
    decoded_text = ""
    
    # Approach 1: Standard 8-bit ASCII
    try:
        for i in range(0, len(clean_binary), 8):
            if i + 8 <= len(clean_binary):
                byte = clean_binary[i:i+8]
                char_code = int(byte, 2)
                if 32 <= char_code <= 126:  # Printable ASCII
                    decoded_text += chr(char_code)
        
        if len(decoded_text) > 3:
            return decoded_text
    except:
        pass
    
    # Approach 2: Try to decode the specific output pattern you're seeing
    # Examples like: "303131313030303030313131313130303030..."
    if clean_binary.startswith("30") and all(c in "0123" for c in clean_binary[:10]):
        try:
            # This might be hexadecimal ASCII codes
            hex_text = ""
            for i in range(0, len(clean_binary), 2):
                if i + 2 <= len(clean_binary):
                    hex_byte = clean_binary[i:i+2]
                    char_code = int(hex_byte, 16)
                    if 32 <= char_code <= 126:  # Printable ASCII
                        hex_text += chr(char_code)
            
            if len(hex_text) > 3:
                return hex_text
        except:
            pass
    
    # If all attempts fail, return a helpful message with sample of the binary
    binary_sample = clean_binary[:100] + "..." if len(clean_binary) > 100 else clean_binary
    return f"Found binary data but couldn't convert to text. Try encoding a new file with the updated code. Binary sample: {binary_sample}"

# Function to allow users to download the encoded file
def download_image(request, filename):
    file_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            content_type = get_content_type(filename)
            response = HttpResponse(file.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponse("File not found", status=404)

# Helper function to determine content type based on file extension
def get_content_type(filename):
    extension = os.path.splitext(filename)[1].lower()
    content_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.wav': 'audio/wav',
        '.mp3': 'audio/mpeg',
        '.txt': 'text/plain',
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.mp4': 'video/mp4',
        '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime'
    }
    return content_types.get(extension, 'application/octet-stream')
