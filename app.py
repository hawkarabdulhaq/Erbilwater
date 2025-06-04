import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ──────────────── CONFIG ────────────────
st.set_page_config(page_title="Well Data App", layout="wide")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Well Map Viewer", "➕ Add New Well", "✏️ Edit Well Data"])

file_path = r"E:\Python\Parez\Wells detailed data.xlsx - Wells detailed data.csv"

# ──────────────── LOAD DATA ────────────────
if not os.path.exists(file_path):
    st.error("CSV file not found. Please check the file path.")
    st.stop()

try:
    df = pd.read_csv(file_path, on_bad_lines='skip')
    df.columns = [col.strip().replace('\n', ' ').replace('\r', '') for col in df.columns]
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ──────────────── CLEAN & PREPARE ────────────────
df["Coordinate X"] = pd.to_numeric(df.get("Coordinate X"), errors="coerce")
df["Coordinate Y"] = pd.to_numeric(df.get("Coordinate Y"), errors="coerce")
df["Depth (m)"] = pd.to_numeric(df.get("Depth (m)"), errors="coerce")
df.rename(columns={"Coordinate X": "lat", "Coordinate Y": "lon"}, inplace=True)
df = df.dropna(subset=["lat", "lon"])

# ──────────────── HOME ────────────────
if page == "Home":
    st.title("Welcome to the Well Data Viewer")
    st.markdown("""
        **Features**:
        - Explore and filter well data
        - Visualize well locations on a map
        - Add, upload, and edit well data
    """)

# ──────────────── MAP VIEWER ────────────────
elif page == "Well Map Viewer":
    st.title("Well Map Viewer")

    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Filters", "📊 Data Table", "🗺️ Map View", "⬆️ Upload CSV"])

    with tab1:
        st.subheader("Filter Options")
        col1, col2 = st.columns(2)
        with col1:
            selected_basin = st.multiselect("Select Basin(s):", df["Basin"].unique(), default=df["Basin"].unique())
        with col2:
            selected_district = st.multiselect("Select Sub-District(s):", df["sub district"].unique(), default=df["sub district"].unique())
        st.success("Filters applied.")

    filtered_df = df[df["Basin"].isin(selected_basin) & df["sub district"].isin(selected_district)]

    with tab2:
        st.subheader("Filtered Well Data")
        st.dataframe(filtered_df)

    with tab3:
        st.subheader("Well Locations on Map")
        fig = px.scatter_mapbox(
            filtered_df,
            lat="lat",
            lon="lon",
            color="Basin",
            hover_name="Well Name",
            hover_data={"Depth (m)": True, "Geological Formation": True, "lat": False, "lon": False},
            zoom=10,
            height=600
        )
        fig.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Upload Additional Well Data (CSV)")
        uploaded_file = st.file_uploader("Upload a CSV file with matching column format", type="csv")
        if uploaded_file:
            try:
                new_data = pd.read_csv(uploaded_file, on_bad_lines='skip')
                new_data.columns = [col.strip().replace('\n', ' ').replace('\r', '') for col in new_data.columns]

                st.write("Preview of uploaded data:")
                st.dataframe(new_data)

                if st.button("Append Uploaded Data to Dataset"):
                    new_data.to_csv(file_path, mode='a', header=False, index=False)
                    st.success("Data uploaded and appended successfully.")
            except Exception as e:
                st.error(f"Failed to upload: {e}")

# ──────────────── ADD NEW WELL ────────────────
elif page == "➕ Add New Well":
    st.title("Add New Well Data")

    tab1, tab2 = st.tabs(["📝 Manual Entry", "📁 Upload CSV"])

    with tab1:
        with st.form("add_form"):
            col1, col2 = st.columns(2)
            with col1:
                well_name = st.text_input("Well Name")
                sub_district = st.text_input("Sub District")
                basin = st.text_input("Basin")
                depth = st.number_input("Depth (m)", step=1.0)
                formation = st.text_input("Geological Formation")
            with col2:
                utm_x = st.number_input("Latitude (Coordinate X)", step=0.0001)
                utm_y = st.number_input("Longitude (Coordinate Y)", step=0.0001)
                elevation = st.number_input("Elevation (Meter)", step=0.1)
                coord_x = utm_x
                coord_y = utm_y

            submitted = st.form_submit_button("Submit")

        if submitted:
            new_entry = pd.DataFrame([{
                "Well Name": well_name,
                "sub district": sub_district,
                "Basin": basin,
                "Depth (m)": depth,
                "Geological Formation": formation,
                "GPS Coor. (UTM) X": utm_x,
                "GPS Coor. (UTM) Y": utm_y,
                "Elevation (Meter)": elevation,
                "Coordinate X": coord_x,
                "Coordinate Y": coord_y
            }])
            try:
                new_entry.to_csv(file_path, mode='a', header=False, index=False)
                st.success(f"Well '{well_name}' added successfully!")
            except Exception as e:
                st.error(f"Failed to add entry: {e}")

    with tab2:
        st.markdown("Upload a **CSV file** with the same structure as the original dataset.")
        uploaded_file = st.file_uploader("Choose CSV file", type=["csv"])
        if uploaded_file is not None:
            try:
                upload_df = pd.read_csv(uploaded_file, on_bad_lines='skip')
                st.write("Preview of uploaded data:")
                st.dataframe(upload_df)

                required_cols = [
                    "Well Name", "sub district", "Basin", "Depth (m)", "Geological Formation",
                    "GPS Coor. (UTM) X", "GPS Coor. (UTM) Y", "Elevation (Meter)",
                    "Coordinate X", "Coordinate Y"
                ]
                missing = [col for col in required_cols if col not in upload_df.columns]
                if missing:
                    st.error(f"Missing required columns: {missing}")
                else:
                    if st.button("Append Uploaded Data to Dataset"):
                        upload_df.to_csv(file_path, mode='a', header=False, index=False)
                        st.success("Uploaded data appended successfully!")
            except Exception as e:
                st.error(f"Error processing file: {e}")

# ──────────────── EDIT WELL DATA ────────────────
elif page == "✏️ Edit Well Data":
    st.title("Edit Existing Well Data")

    try:
        editable_df = pd.read_csv(file_path, on_bad_lines='skip')
        editable_df.columns = [col.strip().replace('\n', ' ').replace('\r', '') for col in editable_df.columns]
    except Exception as e:
        st.error(f"Failed to load data for editing: {e}")
        st.stop()

    st.markdown("You can edit the table below. When you're done, click **Save Changes**.")

    edited_df = st.data_editor(editable_df, use_container_width=True, height=500, key="editable_table")

    if st.button("💾 Save Changes to CSV"):
        try:
            edited_df.to_csv(file_path, index=False)
            st.success("✅ Data updated and saved successfully!")
        except Exception as e:
            st.error(f"Failed to save changes: {e}")
