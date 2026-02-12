import streamlit as st
import pandas as pd
import io

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Excel Merger", page_icon="📂")
st.title("📂 Excel & CSV Merger")
st.write("Upload files. The app automatically finds the header (skipping top blank rows) and merges them.")

# --- 2. SESSION STATE ---
if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

def clear_files():
    st.session_state.uploader_key += 1

# --- 3. SMART READ FUNCTION 🧠 ---
def read_file_auto_header(file):
    """
    Reads a file and automatically finds the header by skipping top blank rows.
    """
    # Step A: Read the raw file with NO header
    if file.name.endswith(".csv"):
        # We read everything as string first to avoid type errors during scan
        df = pd.read_csv(file, header=None, dtype=str)
    else:
        df = pd.read_excel(file, header=None, dtype=str)

    # Step B: Find the first non-empty row
    first_valid_row_index = None
    
    for i, row in df.iterrows():
        # Check if the row has at least 2 non-empty values (to avoid false positives)
        # or just is not completely empty.
        if row.notna().any() and row.str.strip().str.len().sum() > 0:
            first_valid_row_index = i
            break
            
    if first_valid_row_index is None:
        raise ValueError("File appears to be completely empty.")

    # Step C: Reload the file using that row as the header
    # We go back to the start of the file
    file.seek(0) 
    
    if file.name.endswith(".csv"):
        # 'skiprows' tells pandas to jump over the blank lines we found
        df = pd.read_csv(file, header=0, skiprows=first_valid_row_index)
    else:
        df = pd.read_excel(file, header=0, skiprows=first_valid_row_index)
        
    return df

# --- 4. UPLOADER ---
uploaded_files = st.file_uploader(
    "Upload files", 
    type=["csv", "xlsx", "xls"], 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.uploader_key}"
)

# --- 5. MAIN LOGIC ---
if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} files uploaded.")
    
    with st.expander("View Uploaded File List"):
        for file in uploaded_files:
            st.write(f"📄 {file.name}")
            
    col1, col2 = st.columns(2)
    with col1:
        st.button("🗑️ Clear All", on_click=clear_files, use_container_width=True)
    with col2:
        merge_clicked = st.button("🚀 Merge Files", type="primary", use_container_width=True)

    if merge_clicked:
        all_data = []
        progress_bar = st.progress(0)
        
        for i, file in enumerate(uploaded_files):
            try:
                # USE THE NEW SMART FUNCTION
                temp_df = read_file_auto_header(file)
                
                # Clean: Drop rows that are fully empty *after* the header
                temp_df.dropna(how='all', inplace=True)
                
                # Normalize Headers (Strip spaces, lowercase)
                temp_df.columns = temp_df.columns.astype(str).str.strip().str.lower()
                
                all_data.append(temp_df)
                
            except Exception as e:
                st.error(f"❌ Error processing {file.name}: {e}")
            
            progress_bar.progress((i + 1) / len(uploaded_files))

        if all_data:
            # Smart Merge
            final_df = pd.concat(all_data, ignore_index=True, sort=False)
            
            st.success("🎉 Files Merged Successfully!")
            st.write("### Preview")
            st.dataframe(final_df.head())
            
            csv_data = final_df.to_csv(index=False).encode('utf-8')
            
            st.download_button(
                label="📥 Download Merged CSV",
                data=csv_data,
                file_name="merged_master.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.warning("⚠️ No valid data found to merge.")