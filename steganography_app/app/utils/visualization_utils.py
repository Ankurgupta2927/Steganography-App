import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import wave
import cv2
from PIL import Image

def generate_lsb_visualizations():
    """Generate visualizations for LSB steganography across different media types"""
    visualizations = {}
    
    # Image LSB visualization
    plt.figure(figsize=(8, 4))
    plt.subplot(121)
    pixel = np.array([[127, 128, 129], [130, 131, 132]])
    plt.imshow(pixel)
    plt.title('Original Pixel Values')
    plt.subplot(122)
    pixel_modified = np.array([[126, 128, 128], [130, 130, 132]])
    plt.imshow(pixel_modified)
    plt.title('LSB Modified Values')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['lsb_image'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Audio LSB visualization
    plt.figure(figsize=(8, 4))
    t = np.linspace(0, 1, 1000)
    original = np.sin(2*np.pi*5*t)
    modified = original.copy()
    modified[::100] = np.round(modified[::100])  # Modify some samples
    plt.plot(t[:100], original[:100], label='Original')
    plt.plot(t[:100], modified[:100], label='LSB Modified', alpha=0.7)
    plt.title('Audio LSB Encoding')
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['lsb_audio'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Text LSB visualization
    plt.figure(figsize=(8, 3))
    text = "Hello"
    bits = ''.join([format(ord(c), '08b') for c in text])
    plt.text(0.5, 0.7, f'Original Text: "{text}"', ha='center')
    plt.text(0.5, 0.3, f'Binary: {bits}', ha='center')
    plt.axis('off')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['lsb_text'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return visualizations

def generate_dct_visualizations():
    """Generate visualizations for DCT steganography across different media types"""
    visualizations = {}
    
    # Image DCT visualization
    plt.figure(figsize=(12, 4))
    # Original block
    plt.subplot(131)
    block = np.random.rand(8, 8)
    plt.imshow(block, cmap='viridis')
    plt.title('Original 8x8 Block')
    # DCT coefficients
    plt.subplot(132)
    dct = cv2.dct(block)
    plt.imshow(np.log(abs(dct) + 1), cmap='viridis')
    plt.title('DCT Coefficients')
    # Modified DCT
    plt.subplot(133)
    dct_mod = dct.copy()
    dct_mod[5:8, 5:8] *= 0.9  # Modify high frequency coefficients
    plt.imshow(np.log(abs(dct_mod) + 1), cmap='viridis')
    plt.title('Modified DCT')
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dct_image'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Audio DCT visualization
    plt.figure(figsize=(8, 4))
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2*np.pi*10*t) + 0.5*np.sin(2*np.pi*20*t)
    dct = cv2.dct(signal.reshape(-1, 1))
    plt.plot(dct[:50], label='DCT Coefficients')
    plt.title('Audio DCT Transform')
    plt.legend()
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dct_audio'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return visualizations

def generate_dwt_visualizations():
    """Generate visualizations for DWT steganography across different media types"""
    visualizations = {}
    
    # Image DWT visualization
    plt.figure(figsize=(12, 4))
    # Create sample image
    img = np.random.rand(256, 256)
    # Simulate DWT decomposition
    h = img.shape[0]//2
    w = img.shape[1]//2
    dwt = np.zeros_like(img)
    dwt[:h,:w] = cv2.resize(img, (w,h))  # LL
    dwt[:h,w:] = np.random.rand(h,w)*0.5  # LH
    dwt[h:,:w] = np.random.rand(h,w)*0.5  # HL
    dwt[h:,w:] = np.random.rand(h,w)*0.5  # HH
    
    plt.subplot(131)
    plt.imshow(img, cmap='viridis')
    plt.title('Original Image')
    plt.subplot(132)
    plt.imshow(dwt, cmap='viridis')
    plt.title('DWT Decomposition')
    plt.subplot(133)
    dwt_mod = dwt.copy()
    dwt_mod[h:,w:] *= 0.9  # Modify HH subband
    plt.imshow(dwt_mod, cmap='viridis')
    plt.title('Modified DWT')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dwt_image'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    # Audio DWT visualization
    plt.figure(figsize=(10, 6))
    t = np.linspace(0, 1, 1000)
    signal = np.sin(2*np.pi*10*t) + 0.5*np.sin(2*np.pi*20*t)
    
    # Simulate wavelet decomposition
    approx = cv2.resize(signal.reshape(-1, 1), (1, len(signal)//2)).flatten()
    detail = signal[::2] - approx
    
    plt.subplot(311)
    plt.plot(t, signal)
    plt.title('Original Audio Signal')
    plt.subplot(312)
    plt.plot(t[:len(approx)], approx)
    plt.title('Approximation Coefficients')
    plt.subplot(313)
    plt.plot(t[:len(detail)], detail)
    plt.title('Detail Coefficients')
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    visualizations['dwt_audio'] = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return visualizations

def generate_all_visualizations():
    """Generate all technique visualizations"""
    visualizations = {}
    visualizations.update(generate_lsb_visualizations())
    visualizations.update(generate_dct_visualizations())
    visualizations.update(generate_dwt_visualizations())
    return visualizations