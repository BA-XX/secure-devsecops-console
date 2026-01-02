# backend/voice_recognition_service.py

import numpy as np
import base64
import json
from cryptography.fernet import Fernet
import hashlib

def get_encryption_key():
    """Use same encryption as face recognition"""
    from face_recognition_service import get_encryption_key as get_key
    return get_key()

def encrypt_data(data: str) -> str:
    """Encrypt voice data"""
    from face_recognition_service import encrypt_data as encrypt
    return encrypt(data)

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt voice data"""
    from face_recognition_service import decrypt_data as decrypt
    return decrypt(encrypted_data)

def extract_audio_features(audio_base64: str) -> list:
    """
    Extract audio features from base64-encoded audio
    For production, use libraries like librosa, scipy, or speechbrain
    This is a simplified mock implementation
    """
    try:
        # Remove data URL prefix if present
        if ',' in audio_base64:
            audio_base64 = audio_base64.split(',')[1]
        
        # Decode base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Create a simple feature vector based on audio characteristics
        # In production, use proper audio processing (MFCC, mel-spectrogram, etc.)
        
        # Calculate simple statistics as features
        byte_array = np.frombuffer(audio_bytes, dtype=np.uint8)
        
        # Create a feature vector
        features = []
        
        # Statistical features
        features.append(float(np.mean(byte_array)))
        features.append(float(np.std(byte_array)))
        features.append(float(np.max(byte_array)))
        features.append(float(np.min(byte_array)))
        features.append(float(np.median(byte_array)))
        
        # Histogram features (simplified)
        hist, _ = np.histogram(byte_array, bins=50)
        features.extend(hist.astype(float).tolist()[:50])
        
        # FFT features (frequency domain - simplified)
        if len(byte_array) > 512:
            fft = np.fft.fft(byte_array[:512])
            fft_magnitude = np.abs(fft)[:50]
            features.extend(fft_magnitude.astype(float).tolist())
        
        # Pad or truncate to fixed size
        target_size = 200
        if len(features) < target_size:
            features.extend([0.0] * (target_size - len(features)))
        else:
            features = features[:target_size]
        
        return features
    except Exception as e:
        raise ValueError(f"Audio feature extraction failed: {str(e)}")

def enroll_voice(audio_base64: str) -> str:
    """
    Enroll voice sample and return encrypted voice features
    Returns: Encrypted voice features as string
    """
    try:
        # Extract voice features
        voice_features = extract_audio_features(audio_base64)
        
        # Convert to JSON string
        features_json = json.dumps(voice_features)
        
        # Encrypt the features
        encrypted_features = encrypt_data(features_json)
        
        return encrypted_features
    except Exception as e:
        raise ValueError(f"Voice enrollment failed: {str(e)}")

def verify_voice(audio_base64: str, stored_encrypted_features: str, tolerance: float = 0.65) -> dict:
    """
    Verify voice against stored encrypted features
    Returns: dict with 'success' and 'confidence' keys
    """
    try:
        # Extract features from new audio
        new_features = extract_audio_features(audio_base64)
        
        # Decrypt stored features
        decrypted_json = decrypt_data(stored_encrypted_features)
        stored_features = json.loads(decrypted_json)
        
        # Convert to numpy arrays
        new_features_array = np.array(new_features)
        stored_features_array = np.array(stored_features)
        
        # Calculate cosine similarity
        dot_product = np.dot(new_features_array, stored_features_array)
        norm_a = np.linalg.norm(new_features_array)
        norm_b = np.linalg.norm(stored_features_array)
        
        if norm_a == 0 or norm_b == 0:
            similarity = 0
        else:
            similarity = dot_product / (norm_a * norm_b)
        
        # Convert similarity (0-1) to match decision
        is_match = similarity >= (1 - tolerance)
        
        # Calculate confidence (0-100)
        confidence = max(0, min(100, similarity * 100))
        
        return {
            "success": bool(is_match),
            "confidence": float(confidence),
            "similarity": float(similarity),
            "threshold": 1 - tolerance
        }
    except Exception as e:
        raise ValueError(f"Voice verification failed: {str(e)}")

def detect_voice_in_audio(audio_base64: str) -> dict:
    """
    Detect if there's voice/speech in the audio
    Returns: dict with detection info
    """
    try:
        # Remove data URL prefix if present
        if ',' in audio_base64:
            audio_base64 = audio_base64.split(',')[1]
        
        # Decode base64
        audio_bytes = base64.b64decode(audio_base64)
        
        # Simple voice activity detection (VAD)
        # In production, use proper VAD algorithms
        byte_array = np.frombuffer(audio_bytes, dtype=np.uint8)
        
        # Check if there's sufficient audio data
        if len(byte_array) < 1000:
            return {
                "voice_detected": False,
                "message": "Audio sample too short"
            }
        
        # Simple energy-based detection
        energy = np.sum(byte_array.astype(float) ** 2)
        threshold = 1000000  # Adjust based on testing
        
        voice_detected = energy > threshold
        
        return {
            "voice_detected": voice_detected,
            "energy": float(energy),
            "message": "Voice detected" if voice_detected else "No voice detected or audio too quiet"
        }
    except Exception as e:
        return {
            "voice_detected": False,
            "message": f"Error: {str(e)}"
        }