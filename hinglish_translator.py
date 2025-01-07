import streamlit as st
from deep_translator import GoogleTranslator
import re
import pandas as pd
from typing import List, Tuple

class HinglishTranslator:
    def __init__(self):
        self.hindi_pattern = re.compile(r'[\u0900-\u097F]')
        self.english_pattern = re.compile(r'[a-zA-Z]')
        self.hindi_translator = GoogleTranslator(source='auto', target='hi')
        self.english_translator = GoogleTranslator(source='hi', target='en')
        self.auto_translator = GoogleTranslator(source='auto', target='en')
        
    def detect_language_mix(self, text: str) -> Tuple[bool, bool]:
        """Detect if text contains Hindi (Devanagari) and/or English characters."""
        has_hindi = bool(self.hindi_pattern.search(text))
        has_english = bool(self.english_pattern.search(text))
        return has_hindi, has_english
    
    def split_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving separators."""
        sentences = []
        current = []
        
        for char in text:
            current.append(char)
            if char in '.!?।':
                sentences.append(''.join(current))
                current = []
        
        if current:
            sentences.append(''.join(current))
            
        return sentences
    
    def preserve_special_terms(self, text: str) -> Tuple[str, List[str]]:
        """Preserve proper nouns, numbers, and special terms."""
        preserved = []
        
        # Preserve proper nouns (capitalized words)
        pattern = r'\b[A-Z][a-zA-Z]*\b'
        text = re.sub(pattern, lambda m: self._preserve_term(m.group(), preserved), text)
        
        # Preserve numbers and dates
        pattern = r'\b\d+(?:[-/.]\d+)*\b'
        text = re.sub(pattern, lambda m: self._preserve_term(m.group(), preserved), text)
        
        return text, preserved
    
    def _preserve_term(self, term: str, preserved: List[str]) -> str:
        marker = f"PRESERVED_{len(preserved)}"
        preserved.append(term)
        return marker
    
    def restore_preserved_terms(self, text: str, preserved: List[str]) -> str:
        """Restore preserved terms in translated text."""
        for i, term in enumerate(preserved):
            text = text.replace(f"PRESERVED_{i}", term)
        return text
    
    def translate(self, text: str) -> str:
        try:
            if not text.strip():
                return ""
                
            sentences = self.split_sentences(text)
            translated_parts = []
            
            for sentence in sentences:
                if not sentence.strip():
                    continue
                    
                # Detect language mix
                has_hindi, has_english = self.detect_language_mix(sentence)
                
                # Process based on language detection
                if has_hindi and has_english:
                    # Mixed text - translate to Hindi first, then to English
                    hindi_result = self.hindi_translator.translate(sentence)
                    result = self.english_translator.translate(hindi_result)
                elif has_hindi:
                    # Pure Hindi text - translate directly to English
                    result = self.english_translator.translate(sentence)
                else:
                    # Hinglish or English text - try direct translation
                    result = self.auto_translator.translate(sentence)
                
                translated_parts.append(result)
            
            return ' '.join(translated_parts)
            
        except Exception as e:
            st.error(f"Translation error: {str(e)}")
            return "Translation failed. Please try again."

def create_ui():
    st.set_page_config(page_title="Hinglish Translator", page_icon="🔤", layout="wide")
    
    st.markdown("""
        <style>
        .stApp { max-width: 1200px; margin: 0 auto; }
        .main-header { font-size: 2.5rem; text-align: center; color: #1f77b4; margin-bottom: 2rem; }
        .info-box { 
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            border: 1px solid #dee2e6;
        }
        .stTextInput > div > div > input { font-size: 1.2rem; }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">🔤 Hinglish Translator</h1>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("""
            ### Supported Input Types:
            - Pure Hinglish (e.g., "main movie dekhne ja raha hoon")
            - Devanagari Hindi (e.g., "मैं फिल्म देखने जा रहा हूं")
            - Mixed text (combination of Hindi, English, and Hinglish)
        """)
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    create_ui()
    
    if 'translator' not in st.session_state:
        with st.spinner("Initializing translator..."):
            st.session_state.translator = HinglishTranslator()
            st.success("✅ Translator initialized!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Input Text")
        input_text = st.text_area("", height=200, placeholder="Enter text to translate...")
    
    if st.button("Translate", type="primary"):
        if input_text.strip():
            with st.spinner("Translating..."):
                translation = st.session_state.translator.translate(input_text)
                
                with col2:
                    st.subheader("Translation")
                    st.text_area("Original:", value=input_text, height=100, disabled=True)
                    st.text_area("Translation:", value=translation, height=100)
                    
                    if st.button("📋 Copy to Clipboard"):
                        st.write("Translation copied!")
                
                # Update history
                if 'history' not in st.session_state:
                    st.session_state.history = []
                
                st.session_state.history.append({
                    'Original': input_text,
                    'Translation': translation,
                })
        else:
            st.warning("⚠️ Please enter text to translate.")
    
    # Display translation history
    if 'history' in st.session_state and st.session_state.history:
        st.markdown("---")
        st.subheader("📜 Translation History")
        df = pd.DataFrame(st.session_state.history)
        st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()