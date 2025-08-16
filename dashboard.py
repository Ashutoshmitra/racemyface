import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json
import time

# Configure page
st.set_page_config(
    page_title="🚀 Rocket Race Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .winner-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    .stDataFrame {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def load_race_data():
    """Load and process race data from latest results file or fallback sources"""
    try:
        import glob
        import os
        
        race_data = None
        data_source = "Unknown"
        
        # Method 1: Try to load from the dedicated latest results file
        latest_results_file = 'latest_race_results.json'
        if os.path.exists(latest_results_file):
            try:
                with open(latest_results_file, 'r') as f:
                    latest_data = json.load(f)
                
                if latest_data.get('status') == 'completed' and 'results' in latest_data:
                    race_data = latest_data
                    data_source = "Latest Results (Real-time)"
                    st.sidebar.write(f"✅ Loading from real-time results file")
                else:
                    st.sidebar.write(f"⏳ Latest results file exists but no race completed yet")
            except Exception as e:
                st.sidebar.write(f"⚠️ Error reading latest results: {e}")
        
        # Method 2: Fallback to race result files
        if not race_data:
            race_files = glob.glob('rocket_race_results_*.json')
            st.sidebar.write(f"Debug: Found {len(race_files)} race files")
            
            if race_files:
                # Use the most recent race file
                latest_file = max(race_files, key=os.path.getctime)
                st.sidebar.write(f"Loading: {latest_file}")
                data_source = f"Backup File: {os.path.basename(latest_file)}"
                
                with open(latest_file, 'r') as f:
                    race_data = json.load(f)
        
        if race_data:
            # Convert race results to DataFrame
            df = pd.DataFrame(race_data['results'])
            
            # Rename columns to match expected format
            df = df.rename(columns={
                'username': 'Username',
                'fullName': 'Full Name',
                'raceTime': 'Race Time (s)',
                'averageSpeed': 'Speed (km/h)',
                'boostsUsed': 'Boosts Used',
                'collisions': 'Collisions',
                'distanceCovered': 'Distance Covered (km)',
                'rank': 'Rank'
            })
            
            # Clean username format (remove @ if present)
            df['Username'] = df['Username'].str.replace('@', '', regex=False)
            
            # Add race metadata for display
            st.session_state.race_metadata = {
                'race_date': race_data.get('raceDate', 'Unknown'),
                'race_time': race_data.get('raceTime', 'Unknown'),
                'race_duration': race_data.get('actualDuration', 0),
                'total_participants': race_data.get('totalParticipants', 0),
                'finishers': race_data.get('finishers', 0),
                'winner': race_data.get('winner', {}),
                'race_id': race_data.get('raceId', 'Unknown'),
                'data_source': data_source,
                'last_updated': race_data.get('timestamp', 'Unknown')
            }
            
            st.sidebar.write(f"✅ Loaded race data with {len(df)} results from {data_source}")
            return df
            
        else:
            # Fallback: Load CSV and show as participant list (no race data yet)
            df = pd.read_csv('instaExport-2025-08-16T08_51_29.380Z.csv')
            
            # Clean and process the data
            df['Username'] = df['Username'].str.strip()
            df['Full Name'] = df['Full Name'].fillna(df['Username'])
            
            # Add placeholder columns for dashboard compatibility
            df['Race Time (s)'] = np.nan
            df['Speed (km/h)'] = np.nan
            df['Boosts Used'] = 0
            df['Collisions'] = 0
            df['Distance Covered (km)'] = np.nan
            df['Rank'] = range(1, len(df) + 1)
            
            # Indicate no race data available
            st.session_state.race_metadata = {
                'race_date': 'No race yet',
                'race_time': 'Waiting for first race...',
                'race_duration': 0,
                'total_participants': len(df),
                'finishers': 0,
                'winner': {},
                'race_id': 'No race data',
                'data_source': 'CSV participant list',
                'last_updated': 'Never'
            }
            
            st.sidebar.write("❌ No race files found - showing participants")
            return df
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.sidebar.write(f"Error: {e}")
        return pd.DataFrame()

@st.cache_data
def load_image_mapping():
    """Load image mapping data"""
    try:
        with open('image-mapping.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def create_ranking_chart(df, has_race_data=True):
    """Create an interactive ranking chart"""
    top_20 = df.head(20)
    
    fig = go.Figure()
    
    if has_race_data and not df['Race Time (s)'].isna().all():
        # Add bars for race times
        fig.add_trace(go.Bar(
            x=top_20['Username'],
            y=top_20['Race Time (s)'],
            text=top_20['Rank'],
            textposition='outside',
            marker=dict(
                color=top_20['Race Time (s)'],
                colorscale='RdYlGn_r',
                showscale=True,
                colorbar=dict(title="Race Time (s)")
            ),
            hovertemplate="<b>%{x}</b><br>" +
                          "Rank: %{text}<br>" +
                          "Time: %{y:.2f}s<br>" +
                          "<extra></extra>"
        ))
        
        fig.update_layout(
            title="🏆 Top 20 Racers - Race Times",
            xaxis_title="Username",
            yaxis_title="Race Time (seconds)",
            height=500,
            showlegend=False,
            template="plotly_white",
            xaxis=dict(tickangle=45)
        )
    else:
        # Show participant list when no race data
        fig.add_trace(go.Bar(
            x=top_20['Username'],
            y=[1] * len(top_20),  # Equal height bars
            text=top_20['Rank'],
            textposition='outside',
            marker=dict(
                color='lightblue',
                opacity=0.7
            ),
            hovertemplate="<b>%{x}</b><br>" +
                          "Participant #%{text}<br>" +
                          "<extra></extra>"
        ))
        
        fig.update_layout(
            title="👥 Race Participants (Waiting for Race Results)",
            xaxis_title="Username",
            yaxis_title="Participants Ready",
            height=500,
            showlegend=False,
            template="plotly_white",
            xaxis=dict(tickangle=45),
            yaxis=dict(showticklabels=False)
        )
    
    return fig

def create_speed_vs_time_scatter(df):
    """Create speed vs time scatter plot"""
    fig = px.scatter(
        df.head(50), 
        x='Race Time (s)', 
        y='Speed (km/h)',
        size='Boosts Used',
        color='Rank',
        hover_name='Username',
        hover_data=['Full Name', 'Collisions'],
        title="⚡ Speed vs Race Time Analysis (Top 50)",
        color_continuous_scale='RdYlGn_r'
    )
    
    fig.update_layout(height=400, template="plotly_white")
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🚀 EPIC ROCKET RACE DASHBOARD</h1>', unsafe_allow_html=True)
    
    # Add auto-refresh and search
    col_refresh, col_auto, col_search = st.columns([1, 1, 2])
    with col_refresh:
        if st.button("🔄 Refresh Data", help="Click to reload race results"):
            st.rerun()
    
    with col_auto:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False, help="Automatically refresh every 10 seconds to check for new races")
        if auto_refresh:
            # Use Streamlit's built-in rerun capability with delay
            time.sleep(10)
            st.rerun()
    
    # Load data
    df = load_race_data()
    image_mapping = load_image_mapping()
    
    if df.empty:
        st.error("Failed to load race data!")
        return
    
    # Check if we have real race data
    has_race_data = not df['Race Time (s)'].isna().all()
    race_metadata = getattr(st.session_state, 'race_metadata', {})
    
    # Search functionality
    with col_search:
        search_username = st.text_input("🔍 Find Your Rank", 
                                       placeholder="Enter your username...", 
                                       help="Search for your username to see your rank instantly!")
    
    # Show search results if user searched
    if search_username and has_race_data:
        # Search for the user (case insensitive, partial match)
        search_results = df[df['Username'].str.contains(search_username, case=False, na=False)]
        
        if not search_results.empty:
            st.success("🎯 **Search Results:**")
            for _, user in search_results.iterrows():
                # Create a detailed card for each search result
                st.markdown(f"""
                <div class="metric-card" style="margin: 1rem 0; padding: 1.5rem;">
                    <h3>🏆 Rank #{user['Rank']} - @{user['Username']}</h3>
                    <h4>{user['Full Name']}</h4>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("⏱️ Race Time", f"{user['Race Time (s)']:.2f}s")
                with col2:
                    st.metric("⚡ Speed", f"{user['Speed (km/h)']:.1f} km/h")
                with col3:
                    st.metric("🚀 Boosts Used", f"{user['Boosts Used']}")
                with col4:
                    st.metric("💥 Collisions", f"{user['Collisions']}")
                with col5:
                    if user['Rank'] == 1:
                        st.metric("🥇 Status", "WINNER!")
                    elif user['Rank'] <= 3:
                        st.metric("🏅 Status", "PODIUM!")
                    elif user['Rank'] <= 10:
                        st.metric("⭐ Status", "TOP 10!")
                    elif user['Rank'] <= 50:
                        st.metric("🔥 Status", "TOP 50!")
                    else:
                        st.metric("✅ Status", "FINISHED!")
                
                # Performance comparison
                if len(df) > 1:
                    avg_time = df['Race Time (s)'].mean()
                    time_diff = user['Race Time (s)'] - avg_time
                    faster_than = ((df['Race Time (s)'] > user['Race Time (s)']).sum() / len(df)) * 100
                    
                    col_perf1, col_perf2 = st.columns(2)
                    with col_perf1:
                        if time_diff < 0:
                            st.success(f"🚀 {abs(time_diff):.2f}s faster than average!")
                        else:
                            st.info(f"⏳ {time_diff:.2f}s slower than average")
                    with col_perf2:
                        st.info(f"📊 Faster than {faster_than:.1f}% of racers")
                
                st.markdown("---")
        else:
            st.warning(f"❌ No racer found matching '{search_username}'. Try a different search term!")
    elif search_username and not has_race_data:
        # Search in participant list when no race data
        search_results = df[df['Username'].str.contains(search_username, case=False, na=False)]
        if not search_results.empty:
            st.info("🎮 **Participant Found - Ready to Race!**")
            for _, user in search_results.iterrows():
                st.write(f"👤 **@{user['Username']}** ({user['Full Name']}) - Position #{user['Rank']} in participant list")
        else:
            st.warning(f"❌ No participant found matching '{search_username}'.")
    
    # Sidebar search and stats
    st.sidebar.markdown("## 🔍 Quick Search")
    sidebar_search = st.sidebar.text_input("Find Username", placeholder="Quick search...")
    
    if sidebar_search:
        search_results = df[df['Username'].str.contains(sidebar_search, case=False, na=False)]
        if not search_results.empty and has_race_data:
            st.sidebar.markdown("### 🎯 Results:")
            for _, user in search_results.head(3).iterrows():  # Show top 3 matches
                st.sidebar.markdown(f"""
                **@{user['Username']}**  
                🏆 Rank #{user['Rank']}  
                ⏱️ {user['Race Time (s)']:.2f}s  
                🚀 {user['Boosts Used']} boosts  
                💥 {user['Collisions']} crashes
                """)
        elif not search_results.empty:
            st.sidebar.markdown("### 👥 Participants:")
            for _, user in search_results.head(3).iterrows():
                st.sidebar.markdown(f"**@{user['Username']}** - Ready!")
        else:
            st.sidebar.warning("No matches found")
    
    st.sidebar.markdown("## 📊 Race Statistics")
    st.sidebar.metric("Total Participants", len(df))
    
    if has_race_data:
        st.sidebar.metric("Average Race Time", f"{df['Race Time (s)'].mean():.2f}s")
        st.sidebar.metric("Fastest Time", f"{df['Race Time (s)'].min():.2f}s")
        st.sidebar.metric("Total Boosts Used", df['Boosts Used'].sum())
        st.sidebar.metric("Race Duration", f"{race_metadata.get('race_duration', 0):.2f}s")
        st.sidebar.metric("Finishers", f"{race_metadata.get('finishers', 0)}/{race_metadata.get('total_participants', 0)}")
        
        # Show race details
        st.sidebar.markdown(f"""
        ### 🏁 Race Info
        **Date:** {race_metadata.get('race_date', 'Unknown')}  
        **Time:** {race_metadata.get('race_time', 'Unknown')}  
        **Race ID:** {race_metadata.get('race_id', 'Unknown')}  
        **Data Source:** {race_metadata.get('data_source', 'Unknown')}  
        **Last Updated:** {race_metadata.get('last_updated', 'Unknown')}
        """)
    else:
        st.sidebar.info("🎮 Run a race in the game to see live results!")
        st.sidebar.metric("Status", "Waiting for race...")
        st.sidebar.metric("Last Update", race_metadata.get('race_time', 'Never'))
    
    # Winner showcase or waiting message
    if has_race_data and len(df) > 0:
        winner = df.iloc[0]
        st.markdown(f"""
        <div class="winner-card">
            <h2>🏆 LATEST RACE WINNER ✈️</h2>
            <h1>@{winner['Username']}</h1>
            <h3>{winner['Full Name']}</h3>
            <p>🕐 Race Time: {winner['Race Time (s)']:.2f} seconds</p>
            <p>⚡ Average Speed: {winner['Speed (km/h)']:.1f} km/h</p>
            <p>🚀 Boosts Used: {winner['Boosts Used']}</p>
            <p>💥 Collisions: {winner['Collisions']}</p>
            <small>Race Date: {race_metadata.get('race_date', 'Unknown')} at {race_metadata.get('race_time', 'Unknown')}</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="winner-card">
            <h2>🎮 READY TO RACE!</h2>
            <h1>{len(df)} Participants Ready</h1>
            <h3>Waiting for the first race...</h3>
            <p>🎯 Press SPACE in the game to start the countdown!</p>
            <p>🏁 Results will appear here after the race finishes</p>
            <small>Dashboard will auto-update with real race data</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Main dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(create_ranking_chart(df, has_race_data), use_container_width=True)
    
    with col2:
        if has_race_data:
            st.markdown("### 🎯 Quick Stats")
            
            # Top 3 podium
            for i, (_, racer) in enumerate(df.head(3).iterrows()):
                medal = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{medal} Rank {racer['Rank']}</h4>
                    <h3>@{racer['Username']}</h3>
                    <p>{racer['Race Time (s)']:.2f}s</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("### 🎮 Instructions")
            st.markdown("""
            **How to start a race:**
            1. Open `index.html` in your browser
            2. Press **SPACE** to start countdown
            3. Watch the epic rocket race!
            4. Results will automatically save and appear here
            
            **Controls:**
            - `SPACE` - Start race
            - `R` - Reset race
            """)
            
            st.markdown("### 👥 Participants Ready")
            st.metric("Total Racers", len(df))
            st.metric("Waiting for", "First race to start...")
            st.info("🔄 Refresh this page after running a race to see results!")
    
    # Second row
    if has_race_data:
        col3, col4 = st.columns(2)
        
        with col3:
            st.plotly_chart(create_speed_vs_time_scatter(df), use_container_width=True)
        
        with col4:
            # Performance breakdown
            st.markdown("### 🔥 Performance Breakdown")
            
            performance_df = df.head(10)[['Rank', 'Username', 'Race Time (s)', 'Speed (km/h)', 'Boosts Used']].copy()
            performance_df['Race Time (s)'] = performance_df['Race Time (s)'].round(2)
            performance_df['Speed (km/h)'] = performance_df['Speed (km/h)'].round(1)
            
            st.dataframe(
                performance_df,
                use_container_width=True,
                hide_index=True
            )
    else:
        # Show participant preview when no race data
        st.markdown("## 👥 All Participants")
        st.markdown(f"**{len(df)} racers ready to compete!**")
        
        # Show first 20 participants in a nice format
        preview_df = df.head(20)[['Username', 'Full Name']].copy()
        preview_df.index = range(1, len(preview_df) + 1)
        preview_df.index.name = 'Position'
        
        st.dataframe(
            preview_df,
            use_container_width=True
        )
    
    # Full rankings table
    if has_race_data:
        st.markdown("## 📋 Complete Race Results")
        
        # Filters
        col5, col6, col7 = st.columns(3)
        
        with col5:
            show_top = st.selectbox("Show Top", [10, 25, 50, 100, "All"], index=1)
        
        with col6:
            min_time = st.slider("Min Race Time", 
                               float(df['Race Time (s)'].min()), 
                               float(df['Race Time (s)'].max()), 
                               float(df['Race Time (s)'].min()))
        
        with col7:
            max_time = st.slider("Max Race Time", 
                               float(df['Race Time (s)'].min()), 
                               float(df['Race Time (s)'].max()), 
                               float(df['Race Time (s)'].max()))
        
        # Filter data
        filtered_df = df[(df['Race Time (s)'] >= min_time) & (df['Race Time (s)'] <= max_time)]
        
        if show_top != "All":
            filtered_df = filtered_df.head(show_top)
        
        # Display rankings
        display_df = filtered_df[['Rank', 'Username', 'Full Name', 'Race Time (s)', 'Speed (km/h)', 
                                 'Boosts Used', 'Collisions', 'Distance Covered (km)']].copy()
        
        display_df['Race Time (s)'] = display_df['Race Time (s)'].round(2)
        display_df['Speed (km/h)'] = display_df['Speed (km/h)'].round(1)
        display_df['Distance Covered (km)'] = display_df['Distance Covered (km)'].round(2)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.markdown("## 📋 All Participants")
        
        # Filter for participants list
        col5, col6 = st.columns(2)
        
        with col5:
            show_top = st.selectbox("Show Top", [25, 50, 100, "All"], index=0)
        
        with col6:
            search_term = st.text_input("Search Username", placeholder="Type to search...")
        
        # Filter data
        filtered_df = df.copy()
        if search_term:
            filtered_df = filtered_df[filtered_df['Username'].str.contains(search_term, case=False, na=False)]
        
        if show_top != "All":
            filtered_df = filtered_df.head(show_top)
        
        # Display participant list
        display_df = filtered_df[['Username', 'Full Name']].copy()
        display_df.index = range(1, len(display_df) + 1)
        display_df.index.name = 'Position'
        
        st.dataframe(
            display_df,
            use_container_width=True
        )
    
    # Fun facts section
    if has_race_data:
        st.markdown("## 🎉 Fun Race Facts")
        
        col8, col9, col10, col11 = st.columns(4)
        
        with col8:
            fastest_booster = df.loc[df['Boosts Used'].idxmax()]
            st.metric("🚀 Most Boosts Used", 
                     f"@{fastest_booster['Username']}", 
                     f"{fastest_booster['Boosts Used']} boosts")
        
        with col9:
            crash_king = df.loc[df['Collisions'].idxmax()]
            st.metric("💥 Most Collisions", 
                     f"@{crash_king['Username']}", 
                     f"{crash_king['Collisions']} crashes")
        
        with col10:
            distance_leader = df.loc[df['Distance Covered (km)'].idxmax()]
            st.metric("🛣️ Longest Distance", 
                     f"@{distance_leader['Username']}", 
                     f"{distance_leader['Distance Covered (km)']:.2f} km")
        
        with col11:
            speed_demon = df.loc[df['Speed (km/h)'].idxmax()]
            st.metric("⚡ Highest Speed", 
                     f"@{speed_demon['Username']}", 
                     f"{speed_demon['Speed (km/h)']:.1f} km/h")
    else:
        st.markdown("## 🎮 Ready to Race!")
        
        col8, col9, col10, col11 = st.columns(4)
        
        with col8:
            st.metric("🚀 Total Participants", len(df))
        
        with col9:
            st.metric("⏳ Status", "Waiting...")
        
        with col10:
            st.metric("🎯 Next Step", "Start Game")
        
        with col11:
            st.metric("📊 Data Source", "Real Race Results")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <h3>🚀 Epic Rocket Race Dashboard</h3>
        <p>Built with ❤️ using Streamlit | Next race coming soon! 🎮</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()