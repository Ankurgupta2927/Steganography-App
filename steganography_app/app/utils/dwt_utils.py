"""
DWT (Discrete Wavelet Transform) Steganography Utility Module
Provides functions for encoding and decoding messages using DWT steganography
primarily for image files.

DWT-based steganography splits the image into frequency subbands and
embeds the data in these coefficients, which can provide better robustness
against both signal processing operations and noise attacks.
"""

import os
import binascii
import numpy as np
import pywt
import cv2
from PIL import Image
from .lsb_utils import xor_encrypt_decrypt, generate_key


def encode_image(img, message, output_path, key=''):
    """
    Encode a secret message into an image using DWT steganography
    
    Args:
        img: PIL Image object
        message: String message to hide
        output_path: Path to save the output image
        key: Optional encryption key
        
    Returns:
        The encryption key (if generated)
    """
    # Apply simple XOR encryption if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    # Convert PIL Image to numpy array
    img_array = np.array(img)
    
    # Convert to YCbCr colorspace
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        # RGB image
        img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
        y_channel = img_ycbcr[:, :, 0].astype(float)
    else:
        # Grayscale image
        y_channel = img_array.astype(float)
    
    # Apply 2D DWT to Y channel
    coeffs = pywt.dwt2(y_channel, 'haar')
    cA, (cH, cV, cD) = coeffs
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Add terminator
    
    # Check if the image is large enough to hide the message
    max_capacity = min(cH.size, cV.size, cD.size)
    if len(binary_message) > max_capacity:
        raise ValueError(f"Message too large for this image. Max bits: {max_capacity}, Message bits: {len(binary_message)}")
    
    # Embed message in vertical detail coefficients
    for i, bit in enumerate(binary_message):
        if i >= cV.size:
            break
            
        row, col = i // cV.shape[1], i % cV.shape[1]
        
        # Modify coefficient to be even or odd based on bit
        if bit == '0':
            # Make coefficient even
            if int(cV[row, col]) % 2 != 0:
                cV[row, col] = np.floor(cV[row, col])
                if int(cV[row, col]) % 2 != 0:
                    cV[row, col] += 1
        else:
            # Make coefficient odd
            if int(cV[row, col]) % 2 == 0:
                cV[row, col] = np.floor(cV[row, col])
                if int(cV[row, col]) % 2 == 0:
                    cV[row, col] += 1
    
    # Apply inverse DWT
    modified_y_channel = pywt.idwt2((cA, (cH, cV, cD)), 'haar')
    
    # Handle shape mismatch due to DWT
    if modified_y_channel.shape != y_channel.shape:
        modified_y_channel = modified_y_channel[:y_channel.shape[0], :y_channel.shape[1]]
    
    # Update Y channel in YCbCr image
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_ycbcr[:, :, 0] = modified_y_channel.astype(np.uint8)
        # Convert back to RGB
        modified_img = cv2.cvtColor(img_ycbcr, cv2.COLOR_YCrCb2RGB)
    else:
        modified_img = modified_y_channel.astype(np.uint8)
    
    # Convert back to PIL Image and save
    output_img = Image.fromarray(modified_img)
    output_img.save(output_path, 'PNG')
    
    # If no key was provided, generate and return one
    if not key:
        key = generate_key()
    
    return key


def decode_image(img, key=''):
    """
    Decode a hidden message from an image using DWT steganography
    
    Args:
        img: PIL Image object
        key: Optional decryption key
        
    Returns:
        Decoded message string
    """
    # Convert PIL Image to numpy array
    img_array = np.array(img)
    
    # Convert to YCbCr colorspace
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        # RGB image
        img_ycbcr = cv2.cvtColor(img_array, cv2.COLOR_RGB2YCrCb)
        y_channel = img_ycbcr[:, :, 0].astype(float)
    else:
        # Grayscale image
        y_channel = img_array.astype(float)
    
    # Apply DWT
    coeffs = pywt.dwt2(y_channel, 'haar')
    cA, (cH, cV, cD) = coeffs
    
    # Extract binary message from vertical coefficients
    binary_message = ""
    terminator = "00000000"
    
    for i in range(cV.size):
        row, col = i // cV.shape[1], i % cV.shape[1]
        
        # Extract bit based on coefficient parity
        if int(cV[row, col]) % 2 == 0:
            bit = '0'
        else:
            bit = '1'
            
        binary_message += bit
        
        # Check for terminator
        if len(binary_message) >= 8 and binary_message[-8:] == terminator:
            binary_message = binary_message[:-8]  # Remove terminator
            break
    
    # Convert binary to text
    message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            message += chr(int(byte, 2))
    
    # Apply XOR decryption if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    return message


def encode_audio(audio_path, message, output_path, key=''):
    """
    Encode a message into an audio file using DWT steganography
    
    Args:
        audio_path: Path to the audio file
        message: String message to hide
        output_path: Path to save the output audio
        key: Optional encryption key
        
    Returns:
        The encryption key (if generated)
    """
    import wave
    import struct
    
    # Apply simple XOR encryption if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Add terminator
    
    # Open the audio file
    with wave.open(audio_path, 'rb') as audio_file:
        # Get audio parameters
        n_channels = audio_file.getnchannels()
        sample_width = audio_file.getsampwidth()
        framerate = audio_file.getframerate()
        n_frames = audio_file.getnframes()
        
        # Read frames
        frames = audio_file.readframes(n_frames)
    
    # Convert frames to numpy array
    fmt = f"{n_frames}h"
    frame_ints = np.array(struct.unpack(fmt, frames[:n_frames*2]))
    
    # Apply DWT to audio samples
    # We'll use a chunk size that's a power of 2 for better performance
    chunk_size = 1024
    
    # Check if audio is large enough
    n_chunks = len(frame_ints) // chunk_size
    max_bits = n_chunks * 16  # We can embed about 16 bits per chunk
    
    if len(binary_message) > max_bits:
        raise ValueError(f"Message too large for this audio file. Max bits: {max_bits}, Message bits: {len(binary_message)}")
    
    binary_index = 0
    for i in range(0, len(frame_ints) - chunk_size, chunk_size):
        if binary_index >= len(binary_message):
            break
            
        # Get audio chunk
        chunk = frame_ints[i:i+chunk_size]
        
        # Apply DWT
        coeffs = pywt.wavedec(chunk, 'db1', level=3)
        
        # We'll embed in the detail coefficients (cD3)
        cA3, cD3, cD2, cD1 = coeffs
        
        # Embed up to 16 bits in this chunk
        for j in range(min(16, len(binary_message) - binary_index)):
            if binary_index + j >= len(binary_message):
                break
                
            bit = binary_message[binary_index + j]
            
            # Modify coefficient to be even or odd based on bit
            coef_index = j % len(cD3)
            if bit == '0':
                # Make coefficient even
                if int(cD3[coef_index]) % 2 != 0:
                    cD3[coef_index] = np.floor(cD3[coef_index])
                    if int(cD3[coef_index]) % 2 != 0:
                        cD3[coef_index] += 1
            else:
                # Make coefficient odd
                if int(cD3[coef_index]) % 2 == 0:
                    cD3[coef_index] = np.floor(cD3[coef_index])
                    if int(cD3[coef_index]) % 2 == 0:
                        cD3[coef_index] += 1
        
        # Update coefficients
        coeffs = [cA3, cD3, cD2, cD1]
        
        # Apply inverse DWT
        modified_chunk = pywt.waverec(coeffs, 'db1')
        
        # Handle potential length mismatch
        modified_chunk = modified_chunk[:chunk_size]
        
        # Update frame_ints with modified chunk
        frame_ints[i:i+chunk_size] = modified_chunk.astype(np.int16)
        
        binary_index += 16
    
    # Convert back to bytes
    modified_frames = struct.pack(fmt, *frame_ints)
    
    # Create the output audio file
    with wave.open(output_path, 'wb') as output_file:
        output_file.setparams((n_channels, sample_width, framerate, n_frames, 'NONE', 'not compressed'))
        output_file.writeframes(modified_frames[:n_frames*sample_width])
    
    # If no key was provided, generate and return one
    if not key:
        key = generate_key()
    
    return key


def decode_audio(audio_path, key=''):
    """
    Decode a hidden message from an audio file using DWT steganography
    
    Args:
        audio_path: Path to the encoded audio file
        key: Optional decryption key
        
    Returns:
        Decoded message string
    """
    import wave
    import struct
    
    # Open the audio file
    with wave.open(audio_path, 'rb') as audio_file:
        # Get audio parameters
        sample_width = audio_file.getsampwidth()
        n_frames = audio_file.getnframes()
        
        # Read frames
        frames = audio_file.readframes(n_frames)
    
    # Convert frames to numpy array
    fmt = f"{n_frames}h"
    frame_ints = np.array(struct.unpack(fmt, frames[:n_frames*2]))
    
    # Extract bits using DWT
    chunk_size = 1024
    binary_message = ""
    terminator = "00000000"
    
    for i in range(0, len(frame_ints) - chunk_size, chunk_size):
        # Get audio chunk
        chunk = frame_ints[i:i+chunk_size]
        
        # Apply DWT
        coeffs = pywt.wavedec(chunk, 'db1', level=3)
        
        # Extract bits from detail coefficients
        cA3, cD3, cD2, cD1 = coeffs
        
        # Extract up to 16 bits from this chunk
        for j in range(min(16, len(cD3))):
            # Extract bit based on coefficient parity
            if int(cD3[j]) % 2 == 0:
                bit = '0'
            else:
                bit = '1'
                
            binary_message += bit
            
            # Check for terminator
            if len(binary_message) >= 8 and binary_message[-8:] == terminator:
                binary_message = binary_message[:-8]  # Remove terminator
                break
        
        # Check if terminator was found
        if len(binary_message) >= 8 and binary_message[-8:] == terminator:
            binary_message = binary_message[:-8]
            break
    
    # Convert binary to text
    message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            message += chr(int(byte, 2))
    
    # Apply XOR decryption if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    return message


def encode_text(text_path, message, output_path, key=''):
    """
    For text files, DWT isn't directly applicable.
    We'll use the same approach as LSB for text files.
    
    Args:
        text_path: Path to the text file
        message: String message to hide
        output_path: Path to save the output text file
        key: Optional encryption key
        
    Returns:
        The encryption key (if generated)
    """
    # For text files, we'll have to proxy to the LSB method
    from .lsb_utils import encode_text as lsb_encode_text
    return lsb_encode_text(text_path, message, output_path, key)


def decode_text(text_path, key=''):
    """
    Decode message from a text file
    
    Args:
        text_path: Path to the encoded text file
        key: Optional decryption key
        
    Returns:
        Decoded message string
    """
    # Proxy to LSB method for text files
    from .lsb_utils import decode_text as lsb_decode_text
    return lsb_decode_text(text_path, key)


def encode_video(video_path, message, output_path, key=''):
    """
    Encode a message into a video file using DWT steganography
    
    Args:
        video_path: Path to the video file
        message: String message to hide
        output_path: Path to save the output video
        key: Optional encryption key
        
    Returns:
        The encryption key (if generated)
    """
    import cv2
    import tempfile
    
    # Apply simple XOR encryption if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Add terminator
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    
    # Create video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # We'll modify every 5th frame
    frame_count = 0
    binary_index = 0
    
    while cap.isOpened() and binary_index < len(binary_message):
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count % 5 == 0 and binary_index < len(binary_message):
            # Convert frame to YCbCr
            frame_ycbcr = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            y_channel = frame_ycbcr[:, :, 0].astype(float)
            
            # Apply DWT
            coeffs = pywt.dwt2(y_channel, 'haar')
            cA, (cH, cV, cD) = coeffs
            
            # Embed bits in vertical coefficients
            bits_to_embed = min(32, len(binary_message) - binary_index)  # Embed 32 bits per frame
            for i in range(bits_to_embed):
                if binary_index + i >= len(binary_message):
                    break
                    
                bit = binary_message[binary_index + i]
                row, col = i // cV.shape[1], i % cV.shape[1]
                
                # Modify coefficient to be even or odd based on bit
                if bit == '0':
                    # Make coefficient even
                    if int(cV[row, col]) % 2 != 0:
                        cV[row, col] = np.floor(cV[row, col])
                        if int(cV[row, col]) % 2 != 0:
                            cV[row, col] += 1
                else:
                    # Make coefficient odd
                    if int(cV[row, col]) % 2 == 0:
                        cV[row, col] = np.floor(cV[row, col])
                        if int(cV[row, col]) % 2 == 0:
                            cV[row, col] += 1
            
            # Apply inverse DWT
            modified_y_channel = pywt.idwt2((cA, (cH, cV, cD)), 'haar')
            
            # Handle shape mismatch
            if modified_y_channel.shape != y_channel.shape:
                modified_y_channel = modified_y_channel[:y_channel.shape[0], :y_channel.shape[1]]
            
            # Update Y channel
            frame_ycbcr[:, :, 0] = modified_y_channel.astype(np.uint8)
            
            # Convert back to BGR
            frame = cv2.cvtColor(frame_ycbcr, cv2.COLOR_YCrCb2BGR)
            
            binary_index += bits_to_embed
        
        # Write frame to output video
        out.write(frame)
        frame_count += 1
    
    # Finish writing remaining frames without modification
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    
    # Release resources
    cap.release()
    out.release()
    
    # If no key was provided, generate and return one
    if not key:
        key = generate_key()
    
    return key


def decode_video(video_path, key=''):
    """
    Decode a hidden message from a video file using DWT steganography
    
    Args:
        video_path: Path to the encoded video file
        key: Optional decryption key
        
    Returns:
        Decoded message string
    """
    import cv2
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Extract bits from frames
    binary_message = ""
    terminator = "00000000"
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Process every 5th frame
        if frame_count % 5 == 0:
            # Convert to YCbCr
            frame_ycbcr = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            y_channel = frame_ycbcr[:, :, 0].astype(float)
            
            # Apply DWT
            coeffs = pywt.dwt2(y_channel, 'haar')
            cA, (cH, cV, cD) = coeffs
            
            # Extract bits from vertical coefficients
            for i in range(min(32, cV.size)):  # Extract 32 bits per frame
                row, col = i // cV.shape[1], i % cV.shape[1]
                
                # Extract bit based on coefficient parity
                if int(cV[row, col]) % 2 == 0:
                    bit = '0'
                else:
                    bit = '1'
                    
                binary_message += bit
                
                # Check for terminator
                if len(binary_message) >= 8 and binary_message[-8:] == terminator:
                    binary_message = binary_message[:-8]  # Remove terminator
                    cap.release()
                    
                    # Convert binary to text
                    message = ""
                    for i in range(0, len(binary_message), 8):
                        if i + 8 <= len(binary_message):
                            byte = binary_message[i:i+8]
                            message += chr(int(byte, 2))
                    
                    # Apply XOR decryption if key is provided
                    if key:
                        message = xor_encrypt_decrypt(message, key)
                    
                    return message
        
        frame_count += 1
    
    cap.release()
    return "No hidden message found."