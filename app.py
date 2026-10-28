import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Green Transition & Economic Resilience Monitor",
    page_icon="🌍",
    layout="wide"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_excel("master excel.xlsx", sheet_name="master dataset")
    df.columns = df.columns.str.strip()
    return df

try:
    with st.spinner("🔄 Loading master dataset..."):
        df = load_data()
except Exception as e:
    st.error(f"Error loading 'master excel.xlsx': {e}")
    st.stop()

# --- SIDEBAR NAVIGATION & FILTERS ---
st.sidebar.title("🌿 Navigation & Filters")
page = st.sidebar.radio("Go to Section:", [
    "1. Executive Dashboard & Decoupling", 
    "2. Country Transition Segmentation", 
    "3. Environmental Drivers & Risk Model",
    "4. Head-to-Head & What-If Simulator 🚀",
    "5. Global Leaderboard & Heatmap 🏆"
])

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ ML Hyperparameters")
n_clusters_input = st.sidebar.slider("K-Means Clusters (K)", 2, 6, 3)
n_estimators_input = st.sidebar.slider("Random Forest Trees", 50, 300, 100, step=50)

st.sidebar.markdown("---")
st.sidebar.subheader("Global Filters")

regions = df['Region'].dropna().unique().tolist() if 'Region' in df.columns else []
selected_regions = st.sidebar.multiselect("Select Region(s):", regions, default=regions[:3] if regions else [])

if selected_regions:
    filtered_df = df[df['Region'].isin(selected_regions)]
else:
    filtered_df = df

countries = filtered_df['Country Name'].dropna().unique().tolist() if 'Country Name' in df.columns else []
selected_country = st.sidebar.selectbox("Select Focus Country:", ["All Countries"] + countries)

# --- PAGE 1: EXECUTIVE DASHBOARD ---
if page == "1. Executive Dashboard & Decoupling":
    st.title("🌍 Green Transition & Economic Resilience Monitor")
    st.markdown("Analyzing how nations successfully decouple economic growth (GDP) from environmental degradation (CO2 emissions)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_countries = df['Country Name'].nunique() if 'Country Name' in df.columns else 0
        st.metric("Monitored Countries", total_countries)
    with col2:
        avg_gdp_growth = f"{df['GDP Growth (%)'].mean():.2f}%" if 'GDP Growth (%)' in df.columns else "N/A"
        st.metric("Avg GDP Growth", avg_gdp_growth)
    with col3:
        avg_co2_growth = f"{df['CO2 Growth (%)'].mean():.2f}%" if 'CO2 Growth (%)' in df.columns else "N/A"
        st.metric("Avg CO2 Growth", avg_co2_growth)
    with col4:
        avg_risk = f"{df['Transition Risk Score'].mean():.2f}" if 'Transition Risk Score' in df.columns else "N/A"
        st.metric("Avg Transition Risk Score", avg_risk)

    st.markdown("---")

    # --- AUTOMATED KEY POLICY INSIGHTS GENERATOR ---
    st.subheader("💡 Automated Policy & Decoupling Insights")
    if not filtered_df.empty:
        top_gdp_c = filtered_df.loc[filtered_df['GDP Growth (%)'].idxmax()]['Country Name'] if 'GDP Growth (%)' in filtered_df.columns else "N/A"
        lowest_risk_c = filtered_df.loc[filtered_df['Transition Risk Score'].idxmin()]['Country Name'] if 'Transition Risk Score' in filtered_df.columns else "N/A"
        
        top_decoupling = "N/A"
        if 'Decoupling Status' in filtered_df.columns:
            top_decoupling = filtered_df['Decoupling Status'].value_counts().index[0]

        st.info(f"""
        **Executive Summary Insights for Active Region Selection:**
        * 🚀 **Highest Growth Leader:** **{top_gdp_c}** recorded the strongest GDP growth rate within the filtered region(s).
        * 🛡️ **Lowest Transition Risk:** **{lowest_risk_c}** exhibits the best overall resilience and lowest climate transition risk score.
        * 📈 **Dominant Decoupling Class:** The most frequent decoupling profile in this cohort is **'{top_decoupling}'**.
        * 🌐 **Cohort Size:** Analyzing **{filtered_df['Country Name'].nunique()} countries** across **{len(filtered_df)} total recorded country-years**.
        """)
    st.markdown("---")

    if selected_country != "All Countries":
        country_data = df[df['Country Name'] == selected_country]
        st.subheader(f"📊 Deep Dive: {selected_country}")
        
        if 'Year' in country_data.columns and 'GDP Growth (%)' in country_data.columns:
            fig = px.line(
                country_data, x='Year', y=['GDP Growth (%)', 'CO2 Growth (%)'],
                title=f"GDP Growth vs CO2 Growth Over Time — {selected_country}",
                labels={'value': 'Percentage (%)', 'variable': 'Metrics'}
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        # --- RQ1 TOGGLE SECTION ---
        st.subheader("🌐 Economic Growth vs. Environmental Impact (Analysis)")
        view_mode = st.radio("Select View Mode:", ["Decoupling Status Distribution", "GDP Growth (%) vs CO2 Growth (%) Scatter Plot"], horizontal=True)
        
        if view_mode == "Decoupling Status Distribution":
            if 'Decoupling Status' in filtered_df.columns:
                dec_counts = filtered_df['Decoupling Status'].value_counts().reset_index()
                dec_counts.columns = ['Decoupling Status', 'Count']
                fig_pie = px.pie(
                    dec_counts, names='Decoupling Status', values='Count',
                    title="Proportion of Country-Years by Decoupling Classification",
                    hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
        else:
            if 'GDP Growth (%)' in filtered_df.columns and 'CO2 Growth (%)' in filtered_df.columns:
                fig_rq1 = px.scatter(
                    filtered_df.dropna(subset=['GDP Growth (%)', 'CO2 Growth (%)']),
                    x='GDP Growth (%)', y='CO2 Growth (%)', color='Region',
                    hover_name='Country Name', title="Does Economic Growth Lead to Higher CO2 Emissions Growth?"
                )
                st.plotly_chart(fig_rq1, use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Filtered Dataset Explorer")
    st.info(f"Displaying data preview ({len(filtered_df)} total records found for current filters).")
    st.dataframe(filtered_df, use_container_width=True)
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Filtered Data as CSV", data=csv, file_name="green_transition_filtered.csv", mime="text/csv")

# --- PAGE 2: COUNTRY TRANSITION SEGMENTATION (CLUSTERING) ---
elif page == "2. Country Transition Segmentation":
    st.title("📊 Country Transition Segmentation & Energy Analytics")
    
    tab_cl1, tab_cl2, tab_cl3 = st.tabs([
        "Unsupervised K-Means Clustering", 
        "Fossil/Energy Share vs CO2 Emissions", 
        "Energy Intensity Trends"
    ])
    
    with tab_cl1:
        st.markdown(f"Using **K-Means Clustering ($K={n_clusters_input}$)** to group nations into transition profiles based on energy adoption and carbon intensity")
        cluster_features = ['carbon_intensity_elec', 'energy_per_gdp', 'fossil_share_energy']
        cluster_df = filtered_df.dropna(subset=cluster_features).copy()
        
        if len(cluster_df) > 10:
            with st.spinner("🤖 Running K-Means Clustering algorithm..."):
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(cluster_df[cluster_features])
                kmeans = KMeans(n_clusters=n_clusters_input, random_state=42, n_init=10)
                cluster_df['Cluster_ID'] = kmeans.fit_predict(X_scaled)
                cluster_df['Transition Profile'] = "Cluster " + (cluster_df['Cluster_ID'] + 1).astype(str)
                
                fig_cluster = px.scatter(
                    cluster_df, x='energy_per_gdp', y='carbon_intensity_elec',
                    color='Transition Profile', hover_name='Country Name',
                    size_max=10, title=f"Country Clusters ($K={n_clusters_input}$): Carbon Intensity vs Energy per GDP"
                )
                st.plotly_chart(fig_cluster, use_container_width=True)
        else:
            st.warning("Not enough clean data points for clustering with the selected filters.")
            
    with tab_cl2:
        st.subheader("Fossil Fuel Share vs. Annual CO2 Emissions")
        st.markdown("Examining whether higher fossil fuel dependency corresponds directly to elevated carbon output.")
        if 'fossil_share_energy' in filtered_df.columns and 'Annual CO2 emissions' in filtered_df.columns:
            fig_rq2 = px.scatter(
                filtered_df.dropna(subset=['fossil_share_energy', 'Annual CO2 emissions']),
                x='fossil_share_energy', y='Annual CO2 emissions', color='Region',
                hover_name='Country Name', title="Fossil Share Energy (%) vs. Annual CO2 Emissions"
            )
            st.plotly_chart(fig_rq2, use_container_width=True)
        else:
            st.warning("Required columns for RQ2 not available in the dataset.")
            
    with tab_cl3:
        st.subheader("Economic Output Energy Intensity Over Time")
        st.markdown("Analyzing how `energy_per_gdp` evolves historically across regions.")
        if 'energy_per_gdp' in filtered_df.columns and 'Year' in filtered_df.columns:
            fig_e = px.line(
                filtered_df.dropna(subset=['energy_per_gdp', 'Year']),
                x='Year', y='energy_per_gdp', color='Country Name',
                title="Energy Intensity per GDP Over Time by Country"
            )
            st.plotly_chart(fig_e, use_container_width=True)
        else:
            st.warning("Energy per GDP data not available.")

# --- PAGE 3: ENVIRONMENTAL DRIVERS & RISK MODEL ---
elif page == "3. Environmental Drivers & Risk Model":
    st.title("⚙️ Environmental Performance Drivers & Risk Modeling")
    
    target_choice = st.selectbox("Select Machine Learning Target Variable (Risk Modeling):", [
        "Transition Risk Score (Original)", 
        "Annual CO2 emissions (Fossil & Driver Impact on Emissions)"
    ])
    
    target_col = 'Transition Risk Score' if "Transition Risk" in target_choice else 'Annual CO2 emissions'
    
    st.markdown(f"Using a **Random Forest Regressor** ($n\\_estimators={n_estimators_input}$) to evaluate what drives `{target_col}`")
    
    ml_features = ['GDP', 'Inflation', 'Trade', 'population', 'fossil_share_energy']
    ml_df = filtered_df.dropna(subset=ml_features + [target_col]).copy()
    
    if len(ml_df) > 20:
        with st.spinner("🌲 Training Random Forest Regressor & evaluating accuracy..."):
            X = ml_df[ml_features]
            y = ml_df[target_col]
            
            model = RandomForestRegressor(n_estimators=n_estimators_input, random_state=42)
            model.fit(X, y)
            
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
            
            m1, m2 = st.columns(2)
            with m1:
                st.metric("Model $R^2$ Accuracy Score", f"{r2:.4f}")
            with m2:
                st.metric("Model Mean Squared Error (MSE)", f"{mse:.6f}")
                
            st.markdown("---")
            
            importance_df = pd.DataFrame({
                'Feature': ml_features,
                'Importance': model.feature_importances_
            }).sort_values(by='Importance', ascending=True)
            
            fig_imp = px.bar(
                importance_df, x='Importance', y='Feature', orientation='h',
                title=f"Key Drivers of {target_col} (Random Forest Feature Importance)"
            )
            st.plotly_chart(fig_imp, use_container_width=True)
    else:
        st.warning("Insufficient data points in the selected range to train the model.")

# --- PAGE 4: HEAD-TO-HEAD COMPARISON, SIMULATOR & PROJECTIONS ---
elif page == "4. Head-to-Head & What-If Simulator 🚀":
    st.title("⚡ Advanced Analytics: Head-to-Head, Simulator & Projections")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Head-to-Head Country Comparison", 
        "Question C: Energy Use vs CO2 per Capita",
        "Interactive Risk Simulator (ML)", 
        "🔮 2030 / 2050 Net-Zero Future Projection"
    ])
    
    with tab1:
        st.subheader("⚔️ Compare Two Countries Side-by-Side")
        all_countries = df['Country Name'].dropna().unique().tolist()
        c1, c2 = st.columns(2)
        with c1:
            country_a = st.selectbox("Select Country A:", all_countries, index=0)
        with c2:
            country_b = st.selectbox("Select Country B:", all_countries, index=1 if len(all_countries) > 1 else 0)
            
        comp_df = df[df['Country Name'].isin([country_a, country_b])]
        if not comp_df.empty:
            fig_comp = px.line(
                comp_df, x='Year', y='Annual CO2 emissions', color='Country Name',
                title=f"Annual CO2 Emissions Comparison: {country_a} vs {country_b}"
            )
            st.plotly_chart(fig_comp, use_container_width=True)
            
    with tab2:
        st.subheader("Emissions & Economic Scale Per Capita")
        st.markdown("Evaluating per-capita carbon output patterns across regions using dataset metrics.")
        
        c_df = filtered_df.copy()
        if 'Annual CO2 emissions' in c_df.columns and 'population' in c_df.columns and 'GDP' in c_df.columns:
            c_df['CO2_Per_Capita'] = c_df['Annual CO2 emissions'] / c_df['population']
            c_df['GDP_Per_Capita'] = c_df['GDP'] / c_df['population']
            
            fig_c = px.scatter(
                c_df.dropna(subset=['CO2_Per_Capita', 'GDP_Per_Capita']),
                x='GDP_Per_Capita', y='CO2_Per_Capita', color='Region',
                hover_name='Country Name', title="GDP Per Capita vs. CO2 Emissions Per Capita"
            )
            st.plotly_chart(fig_c, use_container_width=True)
        else:
            st.warning("Required columns for per-capita calculation are missing.")

    with tab3:
        st.subheader("🔮 Live 'What-If' Transition Risk Predictor")
        st.markdown("Adjust the sliders below to simulate economic and energy factors and see how the machine learning model predicts the **Transition Risk Score** in real-time.")
        
        ml_features = ['GDP', 'Inflation', 'Trade', 'population', 'fossil_share_energy', 'Annual CO2 emissions']
        ml_df_clean = df.dropna(subset=ml_features + ['Transition Risk Score'])
        
        if len(ml_df_clean) > 20:
            X = ml_df_clean[ml_features]
            y = ml_df_clean['Transition Risk Score']
            sim_model = RandomForestRegressor(n_estimators=n_estimators_input, random_state=42)
            sim_model.fit(X, y)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                s_gdp = st.slider("GDP (USD)", float(X['GDP'].min()), float(X['GDP'].max()), float(X['GDP'].mean()))
                s_inflation = st.slider("Inflation (%)", float(X['Inflation'].min()), float(X['Inflation'].max()), float(X['Inflation'].mean()))
                s_trade = st.slider("Trade (% of GDP)", float(X['Trade'].min()), float(X['Trade'].max()), float(X['Trade'].mean()))
            with col_s2:
                s_pop = st.slider("Population", float(X['population'].min()), float(X['population'].max()), float(X['population'].mean()))
                s_fossil = st.slider("Fossil Share Energy (%)", float(X['fossil_share_energy'].min()), float(X['fossil_share_energy'].max()), float(X['fossil_share_energy'].mean()))
                s_co2 = st.slider("Annual CO2 Emissions", float(X['Annual CO2 emissions'].min()), float(X['Annual CO2 emissions'].max()), float(X['Annual CO2 emissions'].mean()))
                
            input_data = pd.DataFrame([[s_gdp, s_inflation, s_trade, s_pop, s_fossil, s_co2]], columns=ml_features)
            predicted_risk = sim_model.predict(input_data)[0]
            
            st.metric("Predicted Transition Risk Score", f"{predicted_risk:.4f}")
        else:
            st.warning("Not enough data to run the simulator.")

    with tab4:
        st.subheader("📈 2030 / 2050 Trajectory Forecasting")
        st.markdown("Select a country to project historical CO2 emissions forward to **2030** and **2050** using linear trajectory forecasting.")
        
        all_c_proj = df['Country Name'].dropna().unique().tolist()
        proj_country = st.selectbox("Select Target Country for Forecasting:", all_c_proj, key="proj_select")
        
        c_proj_df = df[(df['Country Name'] == proj_country) & df['Annual CO2 emissions'].notna() & df['Year'].notna()].sort_values('Year')
        
        if len(c_proj_df) >= 5:
            X_years = c_proj_df['Year'].values.reshape(-1, 1)
            y_co2 = c_proj_df['Annual CO2 emissions'].values
            
            from sklearn.linear_model import LinearRegression
            trend_model = LinearRegression()
            trend_model.fit(X_years, y_co2)
            
            future_years = np.array(range(int(c_proj_df['Year'].max()) + 1, 2051)).reshape(-1, 1)
            future_preds = trend_model.predict(future_years)
            
            hist_df = pd.DataFrame({'Year': c_proj_df['Year'], 'Annual CO2 emissions': y_co2, 'Type': 'Historical'})
            proj_df = pd.DataFrame({'Year': future_years.flatten(), 'Annual CO2 emissions': future_preds, 'Type': 'Forecasted (2030-2050)'})
            
            combined_trend = pd.concat([hist_df, proj_df], ignore_index=True)
            
            fig_proj = px.line(
                combined_trend, x='Year', y='Annual CO2 emissions', color='Type',
                title=f"Emissions Trajectory & Net-Zero Horizon Target (2030-2050) — {proj_country}",
                line_dash='Type'
            )
            st.plotly_chart(fig_proj, use_container_width=True)
            
            pred_2030 = trend_model.predict([[2030]])[0]
            pred_2050 = trend_model.predict([[2050]])[0]
            
            p1, p2 = st.columns(2)
            with p1:
                st.metric("Projected 2030 Annual CO2 Emissions", f"{max(0, pred_2030):,.2f}")
            with p2:
                st.metric("Projected 2050 Annual CO2 Emissions", f"{max(0, pred_2050):,.2f}")
        else:
            st.warning("Insufficient historical CO2 emissions data points to generate future forecasts for this country.")

# --- PAGE 5: GLOBAL LEADERBOARD & CORRELATION HEATMAP ---
elif page == "5. Global Leaderboard & Heatmap 🏆":
    st.title("🏆 Global Rankings Leaderboard & Statistical Heatmap")
    
    tab_lb, tab_hm = st.tabs(["Global Leaderboard", "Correlation Heatmap"])
    
    with tab_lb:
        st.subheader("📊 Interactive Country Rankings (RQ3 Analysis)")
        metric_choice = st.selectbox("Rank countries based on:", [
            "Transition Risk Score (Lowest Risk = Best)", 
            "GDP Growth (%)", 
            "Annual CO2 emissions (Lowest = Best)"
        ])
        
        top_n = st.slider("Select number of countries to display (Top N):", 5, 30, 10)
        
        if "Transition Risk" in metric_choice:
            val_col = "Transition Risk Score"
            valid_df = df[df[val_col].notna() & (df[val_col] > 0)]
            sorted_df = valid_df.sort_values(by=val_col, ascending=True)
        elif "GDP Growth" in metric_choice:
            val_col = "GDP Growth (%)"
            valid_df = df[val_col].notna()
            sorted_df = valid_df.sort_values(by=val_col, ascending=False)
        else:
            val_col = "Annual CO2 emissions"
            valid_df = df[df[val_col].notna() & (df[val_col] > 0)]
            sorted_df = valid_df.sort_values(by=val_col, ascending=True)
            
        display_df = sorted_df[['Country Name', 'Region', 'IncomeGroup', val_col]].drop_duplicates(subset=['Country Name']).head(top_n)
        display_df.reset_index(drop=True, inplace=True)
        display_df.index = display_df.index + 1
        
        st.dataframe(display_df, use_container_width=True)
        
        fig_lb = px.bar(
            display_df, x='Country Name', y=val_col, color=val_col,
            title=f"Top {top_n} Countries by {metric_choice}",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig_lb, use_container_width=True)
        
    with tab_hm:
        st.subheader("📈 Statistical Correlation Matrix Heatmap")
        st.markdown("Evaluating linear statistical relationships between economic, energy, and environmental variables.")
        
        num_cols = ['GDP', 'Inflation', 'Trade', 'population', 'fossil_share_energy', 'Annual CO2 emissions', 'Transition Risk Score']
        
        hm_df = filtered_df.copy()
        for col in num_cols:
            if col in hm_df.columns:
                hm_df[col] = pd.to_numeric(hm_df[col], errors='coerce')
                
        corr_df = hm_df[num_cols].corr()
        
        if not corr_df.empty:
            fig_corr = px.imshow(
                corr_df, text_auto=True, aspect="auto", color_continuous_scale="RdBu_r",
                title="Feature Correlation Matrix Heatmap"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Insufficient numeric data to generate correlation heatmap.")