"""
Comparison Utility Module for Steganography Techniques
Provides functions for comparing and evaluating different steganography methods
"""

import os
import shutil
import numpy as np
import cv2
import time
import wave
from PIL import Image
import matplotlib
matplotlib.use('Agg')  # Use Agg backend to prevent GUI issues
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from skimage.metrics import structural_similarity, peak_signal_noise_ratio

class SteganoMetrics:
    """Class for comparing and evaluating different steganography techniques"""
    
    TECHNIQUE_MODULES = {
        'lsb': 'lsb_utils',
        'dct': 'dct_utils',
        'dwt': 'dwt_utils'
    }
    
    @staticmethod
    def run_full_comparison(original_file, message, media_type='image', techniques=None, secure_key=''):
        """Run a full comparison of different steganography techniques"""
        if techniques is None:
            techniques = ['lsb', 'dct', 'dwt']
            
        results = {
            'metrics': {},
            'encoded_files': {},
            'execution_time': {},
            'capacity': {},
            'recovery_accuracy': {},
            'stego_paths': {}
        }
        
        temp_dir = os.path.join('temp_stego_files')
        os.makedirs(temp_dir, exist_ok=True)
        
        for technique in techniques:
            try:
                # Import module dynamically
                module = __import__(f'app.utils.{SteganoMetrics.TECHNIQUE_MODULES[technique]}', 
                                 fromlist=['encode_image', 'decode_image'])
                
                output_path = os.path.join(temp_dir, 
                    f"{os.path.splitext(os.path.basename(original_file))[0]}_{technique}"
                    f"{os.path.splitext(original_file)[1]}")
                
                # Measure execution time
                start_time = time.time()
                
                if media_type == 'image':
                    img = Image.open(original_file)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                        
                    # Encode message with secure key
                    key = module.encode_image(img, message, output_path, secure_key)
                    encoded_img = Image.open(output_path)
                    if encoded_img.mode != 'RGB':
                        encoded_img = encoded_img.convert('RGB')
                    
                    # Calculate metrics
                    metrics = SteganoMetrics._calculate_image_metrics_safe(img, encoded_img)
                    
                    # Test message recovery with secure key
                    try:
                        recovered = module.decode_image(encoded_img, key)
                        accuracy = float(len(set(recovered) & set(message))) / float(len(message))
                    except:
                        accuracy = 0.0
                        
                    # Calculate capacity
                    width, height = img.size
                    if technique == 'lsb':
                        capacity = float(width * height * 3) / 8.0
                    elif technique == 'dct':
                        capacity = float(width * height) / 64.0
                    else:
                        capacity = float(width * height) / 32.0
                        
                else:
                    # Handle other media types similarly...
                    continue
                
                # Store results
                results['metrics'][technique] = metrics
                results['encoded_files'][technique] = output_path
                results['execution_time'][technique] = float(time.time() - start_time)
                results['capacity'][technique] = float(capacity)
                results['recovery_accuracy'][technique] = float(accuracy)
                results['stego_paths'][technique] = output_path
                
            except Exception as e:
                print(f"Error processing {technique}: {str(e)}")
                continue
        
        # Generate charts from results
        results['charts'] = SteganoMetrics._generate_charts_safe(results)
        
        return results
    
    @staticmethod
    def _calculate_image_metrics_safe(original_img, stego_img):
        """Safely calculate image quality metrics ensuring scalar outputs"""
        try:
            # Convert to numpy arrays
            orig_arr = np.array(original_img, dtype=np.float64)
            stego_arr = np.array(stego_img, dtype=np.float64)
            
            # Calculate MSE manually for each channel
            mse = 0.0
            for c in range(3):  # RGB channels
                diff = orig_arr[:,:,c] - stego_arr[:,:,c]
                mse += np.mean(diff * diff)
            mse = float(mse) / 3.0
            
            # Calculate PSNR
            if mse < 1e-10:
                psnr = 100.0
            else:
                psnr = float(20.0 * np.log10(255.0 / np.sqrt(mse)))
            
            # Calculate SSIM
            try:
                ssim = float(structural_similarity(
                    orig_arr, 
                    stego_arr,
                    channel_axis=2,
                    data_range=255.0
                ))
            except:
                # Fallback to grayscale comparison
                ssim = float(structural_similarity(
                    cv2.cvtColor(orig_arr.astype(np.uint8), cv2.COLOR_RGB2GRAY),
                    cv2.cvtColor(stego_arr.astype(np.uint8), cv2.COLOR_RGB2GRAY),
                    data_range=255.0
                ))
            
            # Calculate histogram difference
            hist_diff = 0.0
            for c in range(3):
                orig_hist = np.array(original_img.getchannel(c).histogram(), dtype=np.float64)
                stego_hist = np.array(stego_img.getchannel(c).histogram(), dtype=np.float64)
                
                # Normalize histograms
                orig_hist = orig_hist / np.sum(orig_hist)
                stego_hist = stego_hist / np.sum(stego_hist)
                
                # Calculate difference
                hist_diff += float(np.sum(np.abs(orig_hist - stego_hist)))
            
            hist_diff = float(hist_diff / 3.0)
            
            return {
                'mse': float(mse),
                'psnr': float(psnr),
                'ssim': float(ssim),
                'histogram_diff': float(hist_diff)
            }
            
        except Exception as e:
            print(f"Error calculating metrics: {str(e)}")
            return {
                'mse': 0.0,
                'psnr': 0.0,
                'ssim': 0.0,
                'histogram_diff': 0.0
            }
    
    @staticmethod
    def _generate_charts_safe(results):
        """Safely generate comparison charts with proper cleanup"""
        charts = {}
        
        try:
            # Prepare data
            techniques = sorted(list(results['metrics'].keys()))
            
            # PSNR Chart
            if results['metrics']:
                plt.figure(figsize=(8, 6))
                psnr_values = [float(results['metrics'][t]['psnr']) for t in techniques]
                plt.bar(techniques, psnr_values)
                plt.ylabel('PSNR (dB)')
                plt.title('PSNR Comparison')
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                charts['psnr_chart'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # Time Chart
            if results['execution_time']:
                plt.figure(figsize=(8, 6))
                time_values = [float(results['execution_time'][t]) for t in techniques]
                plt.bar(techniques, time_values)
                plt.ylabel('Time (seconds)')
                plt.title('Execution Time Comparison')
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                charts['time_chart'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # Capacity Chart
            if results['capacity']:
                plt.figure(figsize=(8, 6))
                capacity_values = [float(results['capacity'][t])/1024.0 for t in techniques]
                plt.bar(techniques, capacity_values)
                plt.ylabel('Capacity (KB)')
                plt.title('Capacity Comparison')
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                charts['capacity_chart'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
                
            # Accuracy Chart
            if results['recovery_accuracy']:
                plt.figure(figsize=(8, 6))
                accuracy_values = [float(results['recovery_accuracy'][t]) for t in techniques]
                plt.bar(techniques, accuracy_values)
                plt.ylabel('Recovery Accuracy')
                plt.title('Message Recovery Accuracy')
                
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
                charts['accuracy_chart'] = base64.b64encode(buffer.getvalue()).decode()
                plt.close()
            
        except Exception as e:
            print(f"Error generating charts: {str(e)}")
        finally:
            # Clean up all matplotlib resources
            plt.close('all')
        
        return charts