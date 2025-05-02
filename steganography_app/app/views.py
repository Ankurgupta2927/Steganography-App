import os
import shutil
import wave
import struct
import re
import binascii
import json
import time
import numpy as np
import base64
from io import BytesIO
from PIL import Image, ImageChops, ImageEnhance
from skimage.metrics import structural_similarity
import cv2
from django.shortcuts import render
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.utils.http import quote

from .utils import lsb_utils, dct_utils, dwt_utils, comparison_utils

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
        secure_key = request.POST.get('secure_key', '')
        file_type = request.POST.get('file_type', 'image')
        technique = request.POST.get('technique', 'LSB')

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
                encoded_filename = "encoded_" + os.path.basename(converted_file_path)
                encoded_file_path = os.path.join(MEDIA_DIR, encoded_filename)
                
                # Use the selected steganography technique
                if technique.lower() == 'lsb':
                    used_key = lsb_utils.encode_image(img, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dct':
                    used_key = dct_utils.encode_image(img, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dwt':
                    used_key = dwt_utils.encode_image(img, message, encoded_file_path, secure_key)
                
            elif file_type == 'audio' or file_extension in ['.wav']:
                encoded_filename = "encoded_" + os.path.basename(file_path)
                encoded_file_path = os.path.join(MEDIA_DIR, encoded_filename)
                
                # Use the selected steganography technique
                if technique.lower() == 'lsb':
                    used_key = lsb_utils.encode_audio(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dct':
                    used_key = dct_utils.encode_audio(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dwt':
                    used_key = dwt_utils.encode_audio(file_path, message, encoded_file_path, secure_key)
                
            elif file_type == 'text' or file_extension in ['.txt', '.md', '.html', '.css', '.js']:
                encoded_filename = "encoded_" + os.path.basename(file_path)
                encoded_file_path = os.path.join(MEDIA_DIR, encoded_filename)
                
                # Use the selected steganography technique
                if technique.lower() == 'lsb':
                    used_key = lsb_utils.encode_text(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dct':
                    used_key = dct_utils.encode_text(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dwt':
                    used_key = dwt_utils.encode_text(file_path, message, encoded_file_path, secure_key)
                
            elif file_type == 'video' or file_extension in ['.mp4', '.avi', '.mov']:
                encoded_filename = "encoded_" + os.path.basename(file_path)
                encoded_file_path = os.path.join(MEDIA_DIR, encoded_filename)
                
                # Use the selected steganography technique
                if technique.lower() == 'lsb':
                    used_key = lsb_utils.encode_video(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dct':
                    used_key = dct_utils.encode_video(file_path, message, encoded_file_path, secure_key)
                elif technique.lower() == 'dwt':
                    used_key = dwt_utils.encode_video(file_path, message, encoded_file_path, secure_key)
            
            else:
                encoding_error = f"Unsupported file type: {file_extension}"
                
        except Exception as e:
            encoding_error = str(e)
            if os.path.exists(file_path):
                os.remove(file_path)
            return render(request, 'encode.html', {'error': encoding_error})
        
        # Clean up original file if it differs from the encoded file
        if os.path.exists(file_path) and file_path != encoded_file_path:
            os.remove(file_path)
            
        # Clean up converted file if it exists and differs from both original and encoded
        if 'converted_file_path' in locals() and os.path.exists(converted_file_path):
            if converted_file_path != file_path and converted_file_path != encoded_file_path:
                os.remove(converted_file_path)
        
        if encoding_error:
            return render(request, 'encode.html', {'error': encoding_error})
        
        # Get relative URL paths for template
        encoded_file_url = f'/media/{encoded_filename}'
        download_url = f'/download/{encoded_filename}'
        
        return render(request, 'encode.html', {
            'encoded_file_path': encoded_file_url,
            'download_url': download_url,
            'secure_key': used_key,
            'file_type': file_type,
            'technique': technique,
            'message_encoded': True
        })
    
    return render(request, 'encode.html')

# Function to convert uploaded image to PNG if needed
def convert_to_png(img_path):
    """Convert uploaded image to PNG if needed, handling all image types"""
    img = Image.open(img_path)
    if img.format != 'PNG':
        # Convert to RGB/RGBA as needed
        if img.mode == 'P':  # Handle palette images
            img = img.convert('RGBA')
        elif img.mode == 'L':  # Handle grayscale
            img = img.convert('RGB')
        elif img.mode not in ['RGB', 'RGBA']:  # Handle other modes
            img = img.convert('RGB')
            
        new_path = os.path.splitext(img_path)[0] + ".png"
        img.save(new_path, 'PNG')
        os.remove(img_path)  # Remove the original non-PNG file
        return new_path
    return img_path

# Decode a hidden message from a file
def decode(request):
    if request.method == 'POST':
        try:
            file_type = request.POST.get('file_type')
            technique = request.POST.get('technique')
            secure_key = request.POST.get('secure_key', '')
            uploaded_file = request.FILES.get('file')
            
            if not uploaded_file:
                return render(request, 'decode.html', {'error': 'No file was uploaded'})

            # Start timing the decode operation
            start_time = time.time()
            
            # Process based on file type and technique (case-insensitive)
            technique = technique.lower()
            if technique == 'lsb':
                module = lsb_utils
            elif technique == 'dct':
                module = dct_utils
            else:  # dwt
                module = dwt_utils
            
            # Convert uploaded file to appropriate format
            if file_type == 'image':
                img = Image.open(uploaded_file)
                original_img = img.copy()  # Store original for comparison
                message = module.decode_image(img, secure_key)
                
                # Calculate metrics for image files
                metrics = {
                    'psnr': calculate_psnr(original_img, img),
                    'ssim': calculate_ssim(original_img, img),
                    'decode_time': time.time() - start_time,
                    'capacity': calculate_capacity(original_img, technique)
                }
                
                # Generate visual comparison data
                context = {
                    'message': message,
                    'metrics': metrics,
                    'file_type': file_type,
                    'original_image': get_image_data_url(original_img),
                    'stego_image': get_image_data_url(img),
                    'diff_image': generate_difference_map(original_img, img)
                }
                
            elif file_type == 'audio':
                # Save uploaded file temporarily
                temp_path = os.path.join(MEDIA_DIR, 'temp_audio.wav')
                with open(temp_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                
                message = module.decode_audio(temp_path, secure_key)
                metrics = {
                    'decode_time': time.time() - start_time,
                    'capacity': calculate_audio_capacity(temp_path, technique)
                }
                
                os.remove(temp_path)  # Clean up
                context = {'message': message, 'metrics': metrics, 'file_type': file_type}
                
            elif file_type == 'text':
                text_content = uploaded_file.read().decode('utf-8')
                # Save text content temporarily for techniques that require file paths
                temp_path = os.path.join(MEDIA_DIR, 'temp_text.txt')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                
                message = module.decode_text(temp_path, secure_key)
                metrics = {
                    'decode_time': time.time() - start_time,
                    'capacity': len(text_content) // 8  # Rough estimate
                }
                
                os.remove(temp_path)  # Clean up
                context = {'message': message, 'metrics': metrics, 'file_type': file_type}
                
            else:  # video
                # Save uploaded file temporarily
                temp_path = os.path.join(MEDIA_DIR, 'temp_video.mp4')
                with open(temp_path, 'wb') as f:
                    for chunk in uploaded_file.chunks():
                        f.write(chunk)
                
                message = module.decode_video(temp_path, secure_key)
                metrics = {
                    'decode_time': time.time() - start_time,
                    'capacity': calculate_video_capacity(temp_path, technique)
                }
                
                os.remove(temp_path)  # Clean up
                context = {'message': message, 'metrics': metrics, 'file_type': file_type}
            
            return render(request, 'decode.html', context)
            
        except Exception as e:
            return render(request, 'decode.html', {
                'message': f'ERROR: {str(e)}',
                'file_type': file_type if 'file_type' in locals() else None,
                'error': str(e)  # Added to show error in alert
            })
    
    return render(request, 'decode.html')

def calculate_psnr(original_img, stego_img):
    """Calculate Peak Signal-to-Noise Ratio between two images"""
    # Convert to RGB if needed
    if original_img.mode == 'P':
        original_img = original_img.convert('RGBA')
    if stego_img.mode == 'P':
        stego_img = stego_img.convert('RGBA')
        
    if original_img.mode == 'L':
        original_img = original_img.convert('RGB')
    if stego_img.mode == 'L':
        stego_img = stego_img.convert('RGB')
        
    if original_img.mode == 'RGBA':
        background = Image.new('RGB', original_img.size, (255, 255, 255))
        background.paste(original_img, mask=original_img.split()[3])
        original_img = background
        
    if stego_img.mode == 'RGBA':
        background = Image.new('RGB', stego_img.size, (255, 255, 255))
        background.paste(stego_img, mask=stego_img.split()[3])
        stego_img = background
    
    if original_img.size != stego_img.size:
        stego_img = stego_img.resize(original_img.size, Image.Resampling.LANCZOS)
    
    # Convert to numpy arrays
    original_array = np.array(original_img, dtype=np.float64)
    stego_array = np.array(stego_img, dtype=np.float64)
    
    # Calculate MSE for each channel
    mse_values = []
    for channel in range(min(original_array.shape[2], stego_array.shape[2])):
        channel_mse = np.mean(np.square(
            original_array[:,:,channel] - stego_array[:,:,channel]
        ))
        mse_values.append(float(channel_mse))
    
    mse = float(np.mean(mse_values))
    
    if mse < 1e-10:
        return 100.0
    max_pixel = 255.0
    return float(20 * np.log10(max_pixel / np.sqrt(mse)))

def calculate_ssim(original_img, stego_img):
    """Calculate Structural Similarity Index between two images"""
    # Handle different image modes
    if original_img.mode == 'P':
        original_img = original_img.convert('RGBA')
    if stego_img.mode == 'P':
        stego_img = stego_img.convert('RGBA')
        
    if original_img.mode == 'L':
        original_img = original_img.convert('RGB')
    if stego_img.mode == 'L':
        stego_img = stego_img.convert('RGB')
        
    if original_img.mode == 'RGBA':
        background = Image.new('RGB', original_img.size, (255, 255, 255))
        background.paste(original_img, mask=original_img.split()[3])
        original_img = background
        
    if stego_img.mode == 'RGBA':
        background = Image.new('RGB', stego_img.size, (255, 255, 255))
        background.paste(stego_img, mask=stego_img.split()[3])
        stego_img = background
    
    if original_img.size != stego_img.size:
        stego_img = stego_img.resize(original_img.size, Image.Resampling.LANCZOS)
    
    # Convert to numpy arrays
    original_array = np.array(original_img, dtype=np.float64)
    stego_array = np.array(stego_img, dtype=np.float64)
    
    try:
        ssim_value = structural_similarity(
            original_array,
            stego_array,
            channel_axis=2,
            data_range=255.0
        )
    except Exception:
        # Fallback to grayscale comparison if RGB comparison fails
        ssim_value = structural_similarity(
            cv2.cvtColor(original_array.astype(np.uint8), cv2.COLOR_RGB2GRAY),
            cv2.cvtColor(stego_array.astype(np.uint8), cv2.COLOR_RGB2GRAY),
            data_range=255.0
        )
    
    return float(ssim_value)

def calculate_capacity(img, technique):
    """Calculate maximum message capacity for an image"""
    width, height = img.size
    pixels = width * height
    if technique == 'LSB':
        return pixels * 3 // 8  # 3 bits per pixel (RGB)
    elif technique == 'DCT':
        return pixels // 64  # 1 bit per 8x8 block
    else:  # DWT
        return pixels // 32  # Conservative estimate

def calculate_audio_capacity(audio_path, technique):
    """Calculate maximum message capacity for an audio file"""
    with wave.open(audio_path, 'rb') as wav:
        n_frames = wav.getnframes()
        if technique == 'LSB':
            return n_frames // 8
        elif technique == 'DCT':
            return n_frames // 64
        else:  # DWT
            return n_frames // 32

def calculate_video_capacity(video_path, technique):
    """Calculate maximum message capacity for a video file"""
    cap = cv2.VideoCapture(video_path)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    pixels_per_frame = width * height
    if technique == 'LSB':
        return frame_count * pixels_per_frame * 3 // 8
    elif technique == 'DCT':
        return frame_count * pixels_per_frame // 100
    else:  # DWT
        return frame_count * pixels_per_frame // 160

def get_image_data_url(img):
    """Convert PIL Image to base64 data URL"""
    try:
        # Ensure image is in RGB/RGBA mode
        if img.mode not in ['RGB', 'RGBA']:
            img = img.convert('RGB')
            
        # Create a new buffer
        buffered = BytesIO()
        # Save image as PNG with maximum quality
        img.save(buffered, format="PNG", quality=100, optimize=False)
        # Get the base64 encoded string
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error converting image to data URL: {str(e)}")
        return ""

def generate_difference_map(original_img, stego_img):
    """Generate a visual difference map between two images"""
    # Ensure both images are in RGB mode
    if original_img.mode != 'RGB':
        original_img = original_img.convert('RGB')
    if stego_img.mode != 'RGB':
        stego_img = stego_img.convert('RGB')
    
    # Ensure same size
    if original_img.size != stego_img.size:
        stego_img = stego_img.resize(original_img.size, Image.Resampling.LANCZOS)
    
    # Create difference map
    diff = ImageChops.difference(original_img, stego_img)
    
    # Enhance the difference visibility
    enhancer = ImageEnhance.Brightness(diff)
    enhanced_diff = enhancer.enhance(10.0)  # Increased enhancement factor
    
    # Further enhance contrast
    contrast = ImageEnhance.Contrast(enhanced_diff)
    final_diff = contrast.enhance(8.0)
    
    return get_image_data_url(final_diff)

def generate_technique_visualizations():
    """Generate visualizations for each steganography technique"""
    import numpy as np
    import matplotlib.pyplot as plt
    from io import BytesIO
    import base64
    
    visualizations = {}
    
    # LSB Visualization
    plt.figure(figsize=(6, 3))
    # Create a sample 8-bit binary number visualization
    binary = '11010110'
    plt.text(0.5, 0.7, 'Original bit: ' + binary, ha='center', va='center', fontsize=10)
    plt.text(0.5, 0.3, 'LSB modified: ' + binary[:-1] + '1', ha='center', va='center', fontsize=10)
    plt.axis('off')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['lsb_visualization'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # DCT Visualization
    plt.figure(figsize=(6, 3))
    x = np.linspace(0, 4*np.pi, 100)
    y1 = np.cos(x)
    y2 = 0.7*np.cos(x) + 0.3*np.cos(3*x)
    plt.plot(x, y1, label='Original', color='blue', alpha=0.5)
    plt.plot(x, y2, label='DCT Modified', color='orange')
    plt.legend(fontsize=8)
    plt.axis('off')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dct_visualization'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # DWT Visualization
    plt.figure(figsize=(6, 3))
    # Create a simple wavelet decomposition visualization
    t = np.linspace(0, 1, 100)
    s = np.sin(2*np.pi*10*t) * np.exp(-5*t)
    plt.plot(t, s)
    plt.title('Wavelet Decomposition', fontsize=10)
    plt.axis('off')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dwt_visualization'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return visualizations

# Compare different steganography techniques
def compare_techniques(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        message = request.POST.get('message', '')
        secure_key = request.POST.get('secure_key', '')
        file_type = request.POST.get('file_type', 'image')

        # Create directories if they don't exist
        os.makedirs(MEDIA_DIR, exist_ok=True)
        temp_dir = os.path.join(MEDIA_DIR, 'temp_stego_files')
        os.makedirs(temp_dir, exist_ok=True)

        # Save uploaded file directly to temp directory
        fs = FileSystemStorage(location=temp_dir)
        filename = fs.save(file.name, file)
        file_path = os.path.join(temp_dir, filename)
        
        comparison_error = None
        
        try:
            # Convert image to PNG if needed
            if file_type == 'image':
                file_path = convert_to_png(file_path)
            
            # Run comparison for all techniques
            metrics = comparison_utils.SteganoMetrics.run_full_comparison(
                original_file=file_path,
                message=message,
                media_type=file_type,
                secure_key=secure_key
            )
            
            # Format metrics for template display
            formatted_metrics = {
                'psnr': {},
                'ssim': {},
                'capacity': {},
                'encode_time': {},
                'decode_time': {},
                'decoded_messages': {},
                'charts': metrics.get('charts', {})
            }
            
            # Process metrics for each technique
            for technique in ['lsb', 'dct', 'dwt']:
                if 'metrics' in metrics and technique in metrics['metrics']:
                    # Handle PSNR metrics
                    psnr = metrics['metrics'][technique].get('psnr')
                    if isinstance(psnr, (int, float)):
                        formatted_metrics['psnr'][technique.upper()] = round(psnr, 2)
                    
                    # Handle SSIM metrics
                    ssim = metrics['metrics'][technique].get('ssim')
                    if isinstance(ssim, (int, float)):
                        formatted_metrics['ssim'][technique.upper()] = round(ssim, 4)
                
                # Handle capacity
                if 'capacity' in metrics and technique in metrics['capacity']:
                    capacity = metrics['capacity'][technique]
                    formatted_metrics['capacity'][technique.upper()] = f"{capacity:,} bytes"
                
                # Handle execution times
                if 'execution_time' in metrics and technique in metrics['execution_time']:
                    time_value = metrics['execution_time'][technique]
                    formatted_metrics['encode_time'][technique.upper()] = f"{time_value:.4f} sec"
                
                # Handle decoded messages
                if 'recovery_accuracy' in metrics and technique in metrics['recovery_accuracy']:
                    accuracy = metrics['recovery_accuracy'][technique]
                    if isinstance(accuracy, (int, float)):
                        formatted_metrics['decoded_messages'][technique.upper()] = f"Accuracy: {accuracy:.2%}"
                    else:
                        formatted_metrics['decoded_messages'][technique.upper()] = str(accuracy)
            
            # Get paths to encoded files - store just the filenames
            encoded_files = {
                technique.upper(): os.path.basename(path)
                for technique, path in metrics.get('stego_paths', {}).items()
            }
            
            # Move all steganography output files to temp directory
            for technique, path in metrics.get('stego_paths', {}).items():
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    target_path = os.path.join(temp_dir, filename)
                    if path != target_path:  # Only move if not already in temp dir
                        shutil.move(path, target_path)
            
            context = {
                'metrics': formatted_metrics,
                'encoded_files': encoded_files,
                'original_file': os.path.basename(file_path),
                'file_type': file_type
            }
            
            # Generate technique visualizations
            visualizations = generate_technique_visualizations()
            context.update(visualizations)  # Add visualizations to the context
            
            return render(request, 'compare.html', context)
            
        except Exception as e:
            comparison_error = str(e)
            return render(request, 'compare.html', {
                'error': comparison_error,
                'file_type': file_type
            })
        finally:
            # Clean up any remaining files in the root media directory
            if os.path.exists(file_path) and temp_dir not in file_path:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
    
    else:
        # Add visualizations to the initial form view as well
        visualizations = generate_technique_visualizations()
        return render(request, 'compare.html', visualizations)

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

def visualize_techniques(request):
    """Display visualizations for steganography techniques across different media types"""
    from .utils.visualization_utils import generate_all_visualizations
    
    # Generate all visualizations
    visualizations = generate_all_visualizations()
    
    return render(request, 'visualize.html', visualizations)
