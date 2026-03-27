import streamlit as st
import os
from few_shot import FewShotPosts
from post_generator import generate_post
from preprocess import process_posts

# Constants
LENGTH_OPTIONS = ["Short", "Medium", "Long"]
LANGUAGE_OPTIONS = ["English", "Hinglish"]
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw_posts")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed_posts")

# Create directories if they don't exist
for d in [RAW_DIR, PROCESSED_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def main():
    st.set_page_config(page_title="LinkedIn Post AI", page_icon="📝")
    st.title("LinkedIn Post Tool")
    
    tab1, tab2 = st.tabs(["Generator", "Data Manager"])
    
    # --- Tab 1: Generator ---
    with tab1:
        # 1. Select Processed File first
        if os.path.exists(PROCESSED_DIR):
            processed_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]
        else:
            processed_files = []

        if not processed_files:
            st.warning("No processed data found. Please enrich some files in the 'Data Manager' tab.")
            selected_file = None
        else:
            selected_file = st.selectbox("Select Profile/Collection", options=processed_files)
        
        if selected_file:
            file_path = os.path.join(PROCESSED_DIR, selected_file)
            fs = FewShotPosts(file_path)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                tags = fs.get_tags()
                selected_tag = st.selectbox("Topic/Tag", options=tags if tags else ["No tags found"])
            with col2:
                # In larger datasets we might want to dynamic check, but for now use constant
                selected_length = st.selectbox("Length", options=LENGTH_OPTIONS)
            with col3:
                selected_language = st.selectbox("Language", options=LANGUAGE_OPTIONS)

            if st.button("Generate Post"):
                if not tags:
                    st.error("No tags found in this file.")
                else:
                    with st.spinner("Writing post..."):
                        post = generate_post(selected_length, selected_language, selected_tag, fs)
                        st.markdown("### Generated Post")
                        st.text_area("Copy your post", value=post, height=300)

    # --- Tab 2: Data Manager ---
    with tab2:
        st.subheader("Raw Scraped Data (data/raw_posts)")
        
        # List raw files (.json) from raw directory
        if os.path.exists(RAW_DIR):
            raw_files = [f for f in os.listdir(RAW_DIR) if f.endswith(".json")]
        else:
            raw_files = []
        
        if not raw_files:
            st.info("No raw files found in 'data/raw_posts'. Use the extension to scrape some data first!")
        else:
            for rf in raw_files:
                col_name, col_btn = st.columns([3, 1])
                with col_name:
                    st.text(f"📁 {rf}")
                with col_btn:
                    if st.button(f"Process", key=rf):
                        raw_path = os.path.join(RAW_DIR, rf)
                        with st.spinner(f"Enriching {rf}..."):
                            try:
                                processed_path = process_posts(raw_path, PROCESSED_DIR)
                                st.success(f"Processed! Created {os.path.basename(processed_path)}")
                                # Refreshes automatically on next interaction
                            except Exception as e:
                                st.error(f"Error processing {rf}: {e}")

        st.markdown("---")
        st.subheader("Processed Collections (data/processed_posts)")
        if os.path.exists(PROCESSED_DIR):
            processed_files = [f for f in os.listdir(PROCESSED_DIR) if f.endswith(".json")]
            for pf in processed_files:
                st.text(f"✅ {pf}")
            if not processed_files:
                st.info("No processed collections available yet.")
        else:
            st.info("No processed posts found.")

if __name__ == "__main__":
    main()