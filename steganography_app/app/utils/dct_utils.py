"""
DCT (Discrete Cosine Transform) Steganography Utility Module
Provides functions for encoding and decoding messages using DCT steganography
primarily for image files.

The DCT technique modifies frequency coefficients in the image to hide data,
which can provide better robustness against compression compared to LSB.
"""

import os
import binascii
import numpy as np
import cv2
from PIL import Image
import io
from .lsb_utils import xor_encrypt_decrypt, generate_key


def encode_image(img, message, output_path, key=''):
    """
    Encode a secret message into an image using DCT steganography
    
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
    
    # Convert PIL Image to OpenCV format
    img_array = np.array(img)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Check if image is large enough
    height, width = img_cv.shape[:2]
    max_bytes = (height * width) // 64  # Each 8x8 block can hide about 1 byte
    
    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Add terminator
    
    if len(binary_message) > max_bytes * 8:
        raise ValueError(f"Message too large for this image. Max bytes: {max_bytes}, Message bytes: {len(binary_message)//8}")
    
    # Split image into 8x8 blocks for DCT
    img_blocks = []
    for i in range(0, height - height % 8, 8):
        for j in range(0, width - width % 8, 8):
            block = img_cv[i:i+8, j:j+8, 0].astype(np.float32)
            img_blocks.append((i, j, block))
    
    binary_index = 0
    for i, j, block in img_blocks:
        if binary_index >= len(binary_message):
            break
        
        # Apply DCT to block
        dct_block = cv2.dct(block)
        
        # Embed one bit by modifying mid-frequency coefficient
        # We use position (4,5) which is a mid-frequency component
        # This provides a good balance between robustness and imperceptibility
        bit = int(binary_message[binary_index])
        
        # Modify coefficient to be even or odd based on bit
        if bit == 0:
            # Make coefficient even
            if abs(dct_block[4, 5]) % 2 != 0:
                dct_block[4, 5] = np.floor(dct_block[4, 5])
                if dct_block[4, 5] % 2 != 0:
                    dct_block[4, 5] += 1
        else:
            # Make coefficient odd
            if abs(dct_block[4, 5]) % 2 == 0:
                dct_block[4, 5] = np.floor(dct_block[4, 5])
                if dct_block[4, 5] % 2 == 0:
                    dct_block[4, 5] += 1
        
        # Apply inverse DCT
        block_idct = cv2.idct(dct_block)
        
        # Update image with modified block
        img_cv[i:i+8, j:j+8, 0] = block_idct
        
        binary_index += 1
    
    # Convert back to PIL Image and save
    img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
    output_img = Image.fromarray(img_rgb)
    output_img.save(output_path, 'PNG')
    
    # If no key was provided, generate and return one
    if not key:
        key = generate_key()
    
    return key


def decode_image(img, key=''):
    """
    Decode a hidden message from an image using DCT steganography
    
    Args:
        img: PIL Image object
        key: Optional decryption key
        
    Returns:
        Decoded message string
    """
    # Convert PIL Image to OpenCV format
    img_array = np.array(img)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Get dimensions
    height, width = img_cv.shape[:2]
    
    # Extract bits from DCT blocks
    binary_message = ""
    terminator = "00000000"
    
    for i in range(0, height - height % 8, 8):
        for j in range(0, width - width % 8, 8):
            # Get 8x8 block
            block = img_cv[i:i+8, j:j+8, 0].astype(np.float32)
            
            # Apply DCT to block
            dct_block = cv2.dct(block)
            
            # Extract bit from coefficient
            if abs(dct_block[4, 5]) % 2 == 0:
                bit = '0'
            else:
                bit = '1'
            
            binary_message += bit
            
            # Check if we reached the terminator
            if len(binary_message) >= 8 and binary_message[-8:] == terminator:
                binary_message = binary_message[:-8]  # Remove terminator
                break
        else:
            continue
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
    DCT-based encoding for audio is complex. This is a simplified version
    that applies DCT to audio chunks.
    """
    # For audio files, we'll use a hybrid approach with DCT coefficients
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
    
    # Convert frames to numpy array of integers
    fmt = f"{n_frames}h"
    frame_ints = np.array(struct.unpack(fmt, frames[:n_frames*2]))
    
    # Check if audio is large enough to hide the message
    max_bytes = len(frame_ints) // (8 * 8)  # Each 8-sample block can hide 1 bit
    if len(binary_message) > max_bytes:
        raise ValueError(f"Message too large for this audio file. Max bytes: {max_bytes}, Message bytes: {len(binary_message)//8}")
    
    # Split audio into chunks for DCT
    chunk_size = 8
    binary_index = 0
    
    for i in range(0, len(frame_ints) - chunk_size, chunk_size):
        if binary_index >= len(binary_message):
            break
        
        # Get chunk
        chunk = frame_ints[i:i+chunk_size].astype(np.float32)
        
        # Apply DCT
        dct_chunk = cv2.dct(chunk.reshape(1, -1))
        
        # Embed bit in mid-frequency component
        bit = int(binary_message[binary_index])
        
        # Modify coefficient to be even or odd based on bit (using third coefficient)
        if bit == 0:
            # Make coefficient even
            if int(dct_chunk[0, 3]) % 2 != 0:
                dct_chunk[0, 3] = np.floor(dct_chunk[0, 3])
                if int(dct_chunk[0, 3]) % 2 != 0:
                    dct_chunk[0, 3] += 1
        else:
            # Make coefficient odd
            if int(dct_chunk[0, 3]) % 2 == 0:
                dct_chunk[0, 3] = np.floor(dct_chunk[0, 3])
                if int(dct_chunk[0, 3]) % 2 == 0:
                    dct_chunk[0, 3] += 1
        
        # Apply inverse DCT
        chunk_idct = cv2.idct(dct_chunk).reshape(-1)
        
        # Update frame_ints with modified chunk
        frame_ints[i:i+chunk_size] = chunk_idct.astype(np.int16)
        
        binary_index += 1
    
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
    Decode a hidden message from an audio file using DCT steganography
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
    
    # Convert frames to numpy array of integers
    fmt = f"{n_frames}h"
    frame_ints = np.array(struct.unpack(fmt, frames[:n_frames*2]))
    
    # Extract bits from DCT blocks
    binary_message = ""
    chunk_size = 8
    terminator = "00000000"
    
    for i in range(0, len(frame_ints) - chunk_size, chunk_size):
        # Get chunk
        chunk = frame_ints[i:i+chunk_size].astype(np.float32)
        
        # Apply DCT
        dct_chunk = cv2.dct(chunk.reshape(1, -1))
        
        # Extract bit from coefficient
        if int(dct_chunk[0, 3]) % 2 == 0:
            bit = '0'
        else:
            bit = '1'
        
        binary_message += bit
        
        # Check if we reached the terminator
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


def encode_text(text_path, message, output_path, key=''):
    """
    For text files, DCT isn't directly applicable.
    We'll use a modified approach that inserts Unicode characters
    in a pattern determined by DCT coefficients.
    """
    # For text files, we'll have to proxy to the LSB method
    # as DCT doesn't make sense for pure text
    from .lsb_utils import encode_text as lsb_encode_text
    return lsb_encode_text(text_path, message, output_path, key)


def decode_text(text_path, key=''):
    """
    Decode message from a text file that used the DCT-based encoding approach
    """
    # Proxy to LSB method for text files
    from .lsb_utils import decode_text as lsb_decode_text
    return lsb_decode_text(text_path, key)


def encode_video(video_path, message, output_path, key=''):
    """
    DCT-based encoding for videos
    """
    # We'll implement a simplified version that applies DCT to selected frames
    import cv2
    import tempfile
    import shutil
    
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
    
    # Create a temporary directory to store modified frames
    with tempfile.TemporaryDirectory() as temp_dir:
        frame_count = 0
        binary_index = 0
        
        # Create video writer
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # We'll modify every 10th frame to reduce video size and processing time
            if frame_count % 10 == 0 and binary_index < len(binary_message):
                # Split frame into 8x8 blocks and modify only blue channel
                for i in range(0, height - height % 8, 8):
                    for j in range(0, width - width % 8, 8):
                        if binary_index >= len(binary_message):
                            break
                        
                        # Get 8x8 block from blue channel
                        block = frame[i:i+8, j:j+8, 0].astype(np.float32)
                        
                        # Apply DCT
                        dct_block = cv2.dct(block)
                        
                        # Embed bit
                        bit = int(binary_message[binary_index])
                        
                        # Modify coefficient to be even or odd based on bit
                        if bit == 0:
                            # Make coefficient even
                            if abs(dct_block[4, 5]) % 2 != 0:
                                dct_block[4, 5] = np.floor(dct_block[4, 5])
                                if dct_block[4, 5] % 2 != 0:
                                    dct_block[4, 5] += 1
                        else:
                            # Make coefficient odd
                            if abs(dct_block[4, 5]) % 2 == 0:
                                dct_block[4, 5] = np.floor(dct_block[4, 5])
                                if dct_block[4, 5] % 2 == 0:
                                    dct_block[4, 5] += 1
                        
                        # Apply inverse DCT
                        block_idct = cv2.idct(dct_block)
                        
                        # Update frame with modified block
                        frame[i:i+8, j:j+8, 0] = block_idct
                        
                        binary_index += 1
                        
                        if binary_index >= len(binary_message):
                            break
                    if binary_index >= len(binary_message):
                        break
            
            # Write the frame to the output video
            out.write(frame)
            frame_count += 1
        
        # Release resources
        cap.release()
        out.release()
    
    # If no key was provided, generate and return one
    if not key:
        key = generate_key()
    
    return key


def decode_video(video_path, key=''):
    """
    Decode a hidden message from a video using DCT steganography
    """
    import cv2
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Extract bits from DCT blocks
    binary_message = ""
    terminator = "00000000"
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # We'll check every 10th frame (as encoded)
        if frame_count % 10 == 0:
            height, width = frame.shape[:2]
            
            # Process 8x8 blocks in blue channel
            for i in range(0, height - height % 8, 8):
                for j in range(0, width - width % 8, 8):
                    # Get 8x8 block
                    block = frame[i:i+8, j:j+8, 0].astype(np.float32)
                    
                    # Apply DCT
                    dct_block = cv2.dct(block)
                    
                    # Extract bit from coefficient
                    if abs(dct_block[4, 5]) % 2 == 0:
                        bit = '0'
                    else:
                        bit = '1'
                    
                    binary_message += bit
                    
                    # Check if we reached the terminator
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