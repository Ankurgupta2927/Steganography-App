"""
LSB (Least Significant Bit) Steganography Utility Module
Provides functions for encoding and decoding data using the LSB steganography technique
"""

import os
import numpy as np
import secrets
import string
from PIL import Image
import wave
import struct
import cv2


def generate_key(length=16):
    """
    Generate a random encryption key
    
    Args:
        length: Length of the key
        
    Returns:
        Random string key
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def xor_encrypt_decrypt(message, key):
    """
    Encrypt or decrypt a message using XOR with a key
    
    Args:
        message: Message to encrypt/decrypt
        key: Encryption/decryption key
        
    Returns:
        Encrypted/decrypted message
    """
    # Extend the key to match message length
    extended_key = key * (len(message) // len(key) + 1)
    extended_key = extended_key[:len(message)]
    
    # XOR each character with the corresponding key character
    return ''.join(chr(ord(m) ^ ord(k)) for m, k in zip(message, extended_key))


def encode_image(image, message, output_path=None, secure_key=None):
    """
    Encode a message into an image using LSB steganography
    
    Args:
        image: PIL Image object or path to image file
        message: Message to hide
        output_path: Path to save the output image
        secure_key: Optional encryption key
        
    Returns:
        Encryption key used
    """
    # Handle input as either PIL Image or file path
    if isinstance(image, str):
        image = Image.open(image)
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Use provided key or generate a new one
    key = secure_key if secure_key else generate_key()
    
    # Encrypt message if key is provided
    if key:
        message = xor_encrypt_decrypt(message, key)
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '1111111111111110'  # EOF marker
    
    # Check if image can hold the message
    max_bytes = (image.width * image.height * 3) // 8
    message_bytes = len(binary_message) // 8
    
    if message_bytes > max_bytes:
        raise ValueError(f"Message too large. Max size: {max_bytes} bytes, Message size: {message_bytes} bytes")
    
    # Convert image to numpy array for easier manipulation
    img_array = np.array(image)
    
    # Get dimensions for iteration
    height, width, channels = img_array.shape
    
    # Encode message bits into LSBs
    idx = 0
    for h in range(height):
        for w in range(width):
            for c in range(channels):
                if idx < len(binary_message):
                    # Clear the LSB and set it to the message bit
                    img_array[h, w, c] = (img_array[h, w, c] & 0xFE) | int(binary_message[idx])
                    idx += 1
                else:
                    break
    
    # Create a new image from the modified array
    stego_image = Image.fromarray(img_array)
    
    # Save output if path provided
    if output_path:
        stego_image.save(output_path, 'PNG')
    
    return key

def decode_image(image, key=None):
    """
    Decode a message from an image using LSB steganography
    
    Args:
        image: PIL Image object or path to image file
        key: Encryption key used during encoding (optional)
        
    Returns:
        Extracted message
    """
    # Handle input as either PIL Image or file path
    if isinstance(image, str):
        image = Image.open(image)
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Convert image to numpy array
    img_array = np.array(image)
    height, width, channels = img_array.shape
    
    # Extract LSBs
    binary_message = ""
    for h in range(height):
        for w in range(width):
            for c in range(channels):
                binary_message += str(img_array[h, w, c] & 1)
                
                # Check for EOF marker
                if len(binary_message) >= 16 and binary_message[-16:] == '1111111111111110':
                    binary_message = binary_message[:-16]
                    # Convert binary to ASCII
                    message = ""
                    for i in range(0, len(binary_message), 8):
                        if i + 8 <= len(binary_message):
                            byte = binary_message[i:i+8]
                            message += chr(int(byte, 2))
                    
                    # Decrypt message if key is provided
                    if key:
                        message = xor_encrypt_decrypt(message, key)
                    
                    return message
    
    raise ValueError("No hidden message found or EOF marker not detected")


def encode_audio(audio_path, message, output_path):
    """
    Encode a message into an audio file using LSB steganography
    
    Args:
        audio_path: Path to the audio file
        message: Message to hide
        output_path: Path to save the output audio
        
    Returns:
        Encryption key used
    """
    # Generate a random key for added security
    key = generate_key()
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '1111111111111110'  # EOF marker
    
    # Open audio file
    with wave.open(audio_path, 'rb') as audio_file:
        params = audio_file.getparams()
        n_frames = audio_file.getnframes()
        
        # Read all frames
        frames = audio_file.readframes(n_frames)
        
        # Convert frames to sample values
        samples = list(struct.unpack(f"{n_frames * params.nchannels}h", frames))
        
        # Check if audio can hold the message
        max_bytes = len(samples) // 8
        message_bytes = len(binary_message) // 8
        
        if message_bytes > max_bytes:
            raise ValueError(f"Message too large. Max size: {max_bytes} bytes, Message size: {message_bytes} bytes")
        
        # Encode message bits into LSBs of the samples
        for i in range(len(binary_message)):
            if i >= len(samples):
                break
                
            bit = int(binary_message[i])
            
            # Clear the LSB and set it to the message bit
            samples[i] = (samples[i] & 0xFFFE) | bit
        
        # Convert samples back to frames
        stego_frames = struct.pack(f"{len(samples)}h", *samples)
        
        # Write to output file
        with wave.open(output_path, 'wb') as stego_file:
            stego_file.setparams(params)
            stego_file.writeframes(stego_frames)
    
    return key


def decode_audio(audio_path, key=None):
    """
    Decode a message from an audio file using LSB steganography
    
    Args:
        audio_path: Path to the steganographic audio file
        key: Encryption key (not used in simple LSB but kept for consistency)
        
    Returns:
        Extracted message
    """
    # Open audio file
    with wave.open(audio_path, 'rb') as audio_file:
        params = audio_file.getparams()
        n_frames = audio_file.getnframes()
        
        # Read all frames
        frames = audio_file.readframes(n_frames)
        
        # Convert frames to sample values
        samples = list(struct.unpack(f"{n_frames * params.nchannels}h", frames))
        
        # Extract LSBs from the samples
        binary_message = ""
        for i in range(len(samples)):
            binary_message += str(samples[i] & 1)
            
            # Check for EOF marker
            if len(binary_message) >= 16 and binary_message[-16:] == '1111111111111110':
                binary_message = binary_message[:-16]
                break
        
        # Convert binary to ASCII
        message = ""
        for i in range(0, len(binary_message), 8):
            if i + 8 <= len(binary_message):
                byte = binary_message[i:i+8]
                message += chr(int(byte, 2))
    
    return message


def encode_text(text_path, message, output_path):
    """
    Encode a message into a text file using whitespace-based steganography
    
    Args:
        text_path: Path to the text file
        message: Message to hide
        output_path: Path to save the output text
        
    Returns:
        Encryption key used
    """
    # Generate a random key for added security
    key = generate_key()
    
    # Read the original text file
    with open(text_path, 'r', encoding='utf-8') as file:
        text_content = file.read()
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '1111111111111110'  # EOF marker
    
    # Split text into lines
    lines = text_content.split('\n')
    
    # Check if text has enough lines to hide the message
    if len(lines) < len(binary_message):
        raise ValueError(f"Text file too small. Need at least {len(binary_message)} lines, but have {len(lines)} lines.")
    
    # Encode message bits into the end of each line (add a space for 1, nothing for 0)
    for i in range(len(binary_message)):
        if binary_message[i] == '1':
            lines[i] = lines[i] + ' '
    
    # Combine lines back into text
    stego_text = '\n'.join(lines)
    
    # Write to output file
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(stego_text)
    
    return key


def decode_text(text_path, key=None):
    """
    Decode a message from a text file using whitespace-based steganography
    
    Args:
        text_path: Path to the steganographic text file
        key: Encryption key (not used in simple whitespace steganography but kept for consistency)
        
    Returns:
        Extracted message
    """
    # Read the stego text file
    with open(text_path, 'r', encoding='utf-8') as file:
        stego_text = file.read()
    
    # Split text into lines
    lines = stego_text.split('\n')
    
    # Extract bits from the end of each line
    binary_message = ""
    for line in lines:
        if line.endswith(' '):
            binary_message += '1'
        else:
            binary_message += '0'
        
        # Check for EOF marker
        if len(binary_message) >= 16 and binary_message[-16:] == '1111111111111110':
            binary_message = binary_message[:-16]
            break
    
    # Convert binary to ASCII
    message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            message += chr(int(byte, 2))
    
    return message


def encode_video(video_path, message, output_path):
    """
    Encode a message into a video file using LSB steganography
    
    Args:
        video_path: Path to the video file
        message: Message to hide
        output_path: Path to save the output video
        
    Returns:
        Encryption key used
    """
    # Generate a random key for added security
    key = generate_key()
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '1111111111111110'  # EOF marker
    
    # Open video file
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Create output video writer
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Get the first frame for encoding
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Failed to read video file")
    
    # Flatten the frame for easier manipulation
    flattened = frame.flatten()
    
    # Check if frame can hold the message
    max_bytes = len(flattened) // 8
    message_bytes = len(binary_message) // 8
    
    if message_bytes > max_bytes:
        raise ValueError(f"Message too large. Max size: {max_bytes} bytes, Message size: {message_bytes} bytes")
    
    # Encode message bits into LSBs of the flattened array
    idx = 0
    for i in range(len(binary_message)):
        bit = int(binary_message[i])
        
        # Clear the LSB and set it to the message bit
        flattened[idx] = (flattened[idx] & 0xFE) | bit
        idx += 1
    
    # Reshape back to original dimensions
    stego_frame = flattened.reshape(frame.shape)
    
    # Write the stego frame
    out.write(stego_frame.astype(np.uint8))
    
    # Copy the rest of the frames
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
    
    # Release resources
    cap.release()
    out.release()
    
    return key


def decode_video(video_path, key=None):
    """
    Decode a message from a video file using LSB steganography
    
    Args:
        video_path: Path to the steganographic video file
        key: Encryption key (not used in simple LSB but kept for consistency)
        
    Returns:
        Extracted message
    """
    # Open video file
    cap = cv2.VideoCapture(video_path)
    
    # Get the first frame for decoding
    ret, frame = cap.read()
    if not ret:
        raise ValueError("Failed to read video file")
    
    # Flatten the frame for easier manipulation
    flattened = frame.flatten()
    
    # Extract LSBs from the flattened array
    binary_message = ""
    for i in range(len(flattened)):
        binary_message += str(flattened[i] & 1)
        
        # Check for EOF marker
        if len(binary_message) >= 16 and binary_message[-16:] == '1111111111111110':
            binary_message = binary_message[:-16]
            break
    
    # Convert binary to ASCII
    message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            message += chr(int(byte, 2))
    
    # Release resources
    cap.release()
    
    return message