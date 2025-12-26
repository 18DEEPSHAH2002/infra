import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Dashboard Infrastructure Project Progress",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    h2 {
        color: #1f77b4;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load data from Google Sheets"""
    sheet_id = "11mKnJQOSZ6WJApYRaYtJ91gQmMivoIEs0LPcmBw91Kg"
    gid = "1130720003"
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    try:
        response = requests.get(export_url, timeout=10)
        df = pd.read_csv(StringIO(response.text))
        
        # Column mapping
        columns_mapping = {
            '  ': 'SNO',
            'To be filled by the departments': 'SNO_Detail',
            'Unnamed: 2': 'Agency',
            'Unnamed: 3': 'Division',
            'Unnamed: 4': 'AC_Name',
            'Unnamed: 5': 'Project_Name',
            'Unnamed: 6': 'Description',
            'Unnamed: 7': 'Project_Status',
            'Unnamed: 8': 'Begin_Date',
            'Unnamed: 9': 'Physical_Progress',
            'Unnamed: 10': 'Start_Date',
            'Unnamed: 11': 'Start_Date2',
            'Unnamed: 12': 'Proposed_Completion_Date',
            'Unnamed: 13': 'UC_Status',
            'Unnamed: 14': 'Stuck_Reason',
            'Departments need not to fill': 'Duration_Days',
            'Unnamed: 16': 'Work_Completion_PerDay',
            'Unnamed: 17': 'Project_Days_Since_Start',
            'Unnamed: 18': 'Projected_Completion_Pct',
            'Unnamed: 19': 'Current_Status',
            'Unnamed: 20': 'Expenditure_Pct',
            'Unnamed: 21': 'Remarks'
        }
        
        df = df.rename(columns=columns_mapping)
        
        # Select relevant columns
        relevant_cols = ['SNO', 'Agency', 'Division', 'Project_Name', 'Description', 
                        'Project_Status', 'Physical_Progress', 'UC_Status', 
                        'Current_Status', 'Projected_Completion_Pct', 'Expenditure_Pct', 'Stuck_Reason']
        
        df = df[relevant_cols]
        
        # Clean percentages
        for col in ['Physical_Progress', 'Projected_Completion_Pct', 'Expenditure_Pct']:
            df[col] = df[col].astype(str).str.rstrip('%').str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Filter data
        df = df[df['Project_Name'].notna() & (df['Project_Name'] != '') & 
                (df['Project_Name'] != 'Project Name')]
        df = df[df['SNO'].notna() & (df['SNO'] != '') & (df['SNO'] != 'Super S.No.')]
        df = df[df['Agency'] != 'Project Implementation Agency/ Department']
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

# Load data
df = load_data()

# Title
st.markdown("# 📊 Ludhiana Infrastructure Project Progress Dashboard")
st.markdown("**Real-time tracking of all ongoing development projects across departments**")

if not df.empty:
    # Filters in sidebar
    st.sidebar.markdown("## 🔍 Filters")
    
    agencies = ['All'] + sorted(df['Agency'].unique().tolist())
    selected_agency = st.sidebar.selectbox("Select Agency/Department", agencies)
    
    # Filter data based on selection
    if selected_agency != 'All':
        df_filtered = df[df['Agency'] == selected_agency].copy()
    else:
        df_filtered = df.copy()
    
    # Additional filter for project status
    project_statuses = ['All'] + sorted(df_filtered['Project_Status'].unique().tolist())
    selected_status = st.sidebar.selectbox("Select Project Status", project_statuses)
    
    if selected_status != 'All':
        df_filtered = df_filtered[df_filtered['Project_Status'] == selected_status]
    
    # Display KPIs
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Projects", len(df_filtered), delta=None)
    
    with col2:
        completed = len(df_filtered[df_filtered['Project_Status'] == 'Completed'])
        st.metric("Completed", completed, f"{(completed/len(df_filtered)*100):.1f}%")
    
    with col3:
        ongoing = len(df_filtered[df_filtered['Project_Status'] == 'Ongoing'])
        st.metric("Ongoing", ongoing, f"{(ongoing/len(df_filtered)*100):.1f}%")
    
    with col4:
        delayed = len(df_filtered[df_filtered['Current_Status'] == 'Project Delaid'])
        st.metric("Delayed", delayed, f"{(delayed/len(df_filtered)*100):.1f}%")
    
    with col5:
        avg_progress = df_filtered['Physical_Progress'].mean()
        st.metric("Avg Progress", f"{avg_progress:.1f}%", delta=None)
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Analytics", "📋 Project List", "🏗️ By Agency", "⚠️ At Risk", "📍 By Division"
    ])
    
    # Tab 1: Analytics
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # Project Status Distribution
            status_counts = df_filtered['Project_Status'].value_counts()
            fig_status = go.Figure(data=[go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                hole=.3,
                marker=dict(colors=['#2ecc71', '#e74c3c', '#f39c12', '#3498db'])
            )])
            fig_status.update_layout(
                title="Project Status Distribution",
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_status, use_container_width=True)
        
        with col2:
            # Current Status Distribution
            current_status_counts = df_filtered[df_filtered['Current_Status'].isin(
                ['Project Delaid', 'Already Completed'])]['Current_Status'].value_counts()
            
            fig_current = go.Figure(data=[go.Pie(
                labels=current_status_counts.index,
                values=current_status_counts.values,
                marker=dict(colors=['#e74c3c', '#2ecc71'])
            )])
            fig_current.update_layout(
                title="Project Completion Status",
                height=400,
                showlegend=True
            )
            st.plotly_chart(fig_current, use_container_width=True)
        
        # Physical Progress Distribution
        col1, col2 = st.columns(2)
        
        with col1:
            # Progress range histogram
            fig_progress = px.histogram(
                df_filtered,
                x='Physical_Progress',
                nbins=10,
                title="Physical Progress Distribution",
                labels={'Physical_Progress': 'Progress (%)'},
                color_discrete_sequence=['#3498db']
            )
            fig_progress.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with col2:
            # UC Status Distribution
            uc_counts = df_filtered['UC_Status'].value_counts()
            fig_uc = px.bar(
                x=uc_counts.index,
                y=uc_counts.values,
                title="UC (Utilization Certificate) Status",
                labels={'x': 'UC Status', 'y': 'Count'},
                color=uc_counts.values,
                color_continuous_scale='Viridis'
            )
            fig_uc.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_uc, use_container_width=True)
    
    # Tab 2: Project List
    with tab2:
        st.subheader("Detailed Project Information")
        
        # Display table with key columns
        display_df = df_filtered[[
            'Project_Name', 'Description', 'Agency', 'Division',
            'Project_Status', 'Physical_Progress', 'Current_Status', 'UC_Status'
        ]].copy()
        
        display_df.columns = ['Project', 'Description', 'Agency', 'Division', 
                             'Status', 'Progress %', 'Current Status', 'UC Status']
        
        # Format progress column
        display_df['Progress %'] = display_df['Progress %'].apply(
            lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
        )
        
        st.dataframe(display_df, use_container_width=True, height=600)
        
        # Download option
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"projects_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Tab 3: By Agency
    with tab3:
        st.subheader("Project Distribution by Agency")
        
        agency_stats = df_filtered.groupby('Agency').agg({
            'Project_Name': 'count',
            'Physical_Progress': 'mean',
            'Project_Status': lambda x: (x == 'Completed').sum()
        }).round(2)
        
        agency_stats.columns = ['Total Projects', 'Avg Progress %', 'Completed']
        agency_stats = agency_stats.sort_values('Total Projects', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_agency = px.bar(
                agency_stats.reset_index(),
                x='Agency',
                y='Total Projects',
                title='Projects by Agency',
                color='Total Projects',
                color_continuous_scale='Blues',
                height=400
            )
            fig_agency.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_agency, use_container_width=True)
        
        with col2:
            fig_progress_agency = px.bar(
                agency_stats.reset_index(),
                x='Agency',
                y='Avg Progress %',
                title='Average Progress by Agency',
                color='Avg Progress %',
                color_continuous_scale='Greens',
                height=400
            )
            fig_progress_agency.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_progress_agency, use_container_width=True)
        
        st.dataframe(agency_stats, use_container_width=True)
    
    # Tab 4: At Risk Projects
    with tab4:
        st.subheader("⚠️ Projects Requiring Attention")
        
        # Projects with low progress
        at_risk = df_filtered[
            (df_filtered['Physical_Progress'] < 50) | 
            (df_filtered['Current_Status'] == 'Project Delaid')
        ].copy()
        
        if not at_risk.empty:
            at_risk_display = at_risk[[
                'Project_Name', 'Description', 'Physical_Progress',
                'Current_Status', 'UC_Status', 'Stuck_Reason'
            ]].copy()
            
            at_risk_display.columns = [
                'Project', 'Description', 'Progress %', 'Status', 'UC Status', 'Stuck Reason'
            ]
            
            at_risk_display['Progress %'] = at_risk_display['Progress %'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A"
            )
            
            st.warning(f"🔴 {len(at_risk)} projects identified as at-risk")
            st.dataframe(at_risk_display, use_container_width=True, height=500)
            
            # Risk visualization
            fig_risk = px.scatter(
                at_risk,
                x='Physical_Progress',
                y='Projected_Completion_Pct',
                size='Physical_Progress',
                color='Current_Status',
                hover_data=['Project_Name'],
                title='At-Risk Projects: Progress vs Projected Completion',
                labels={
                    'Physical_Progress': 'Actual Progress (%)',
                    'Projected_Completion_Pct': 'Projected Completion (%)'
                },
                height=400
            )
            st.plotly_chart(fig_risk, use_container_width=True)
        else:
            st.success("✅ All projects are progressing well!")
    
    # Tab 5: By Division
    with tab5:
        st.subheader("Projects by Division/Circle")
        
        division_filter = df_filtered['Division'].dropna().unique()
        
        if len(division_filter) > 0:
            division_stats = df_filtered[df_filtered['Division'].notna()].groupby('Division').agg({
                'Project_Name': 'count',
                'Physical_Progress': 'mean',
                'Project_Status': lambda x: (x == 'Completed').sum()
            }).round(2)
            
            division_stats.columns = ['Total Projects', 'Avg Progress %', 'Completed']
            division_stats = division_stats.sort_values('Total Projects', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_division = px.bar(
                    division_stats.reset_index(),
                    x='Division',
                    y='Total Projects',
                    title='Projects by Division',
                    color='Total Projects',
                    color_continuous_scale='Purples',
                    height=400
                )
                fig_division.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_division, use_container_width=True)
            
            with col2:
                fig_div_progress = px.bar(
                    division_stats.reset_index(),
                    x='Division',
                    y='Avg Progress %',
                    title='Average Progress by Division',
                    color='Avg Progress %',
                    color_continuous_scale='Oranges',
                    height=400
                )
                fig_div_progress.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_div_progress, use_container_width=True)
            
            st.dataframe(division_stats, use_container_width=True)
        else:
            st.info("No division information available")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    **Dashboard Features:**
    - 📊 Real-time analytics from Google Sheets
    - 🔍 Filter by Agency and Project Status
    - 📈 Visual charts and metrics
    - ⚠️ At-risk project identification
    - 📥 Export data as CSV
    
    **Last Updated:** """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
else:
    st.error("Unable to load project data. Please check the sheet URL and permissions.")
