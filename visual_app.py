#!/usr/bin/env python
# coding: utf-8

# Import modules
import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
import matplotlib.pyplot as plt

# SETTING PAGE CONFIG TO WIDE MODE AND ADDING A TITLE AND FAVICON
st.set_page_config(page_title="Managed Charging Enrollment Demo",
                   layout="wide",
                   initial_sidebar_state="auto",
                   page_icon=":battery:")

# Load Enrollment Data
@st.experimental_singleton
def load_data():
    # Read in latest enrollment data from SDV team
    df = pd.read_csv("enrollments.csv")
    
    # Remove users that failed to enroll
    df = df[df["utility_status"] != "Failed"].reset_index(drop=True)
    
    # Extract out lat/lon for each enrolled user
    df["_home_location"] = df["_home_location"].astype(str)
    df = df[df["_home_location"] != "nan"].reset_index(drop=True)
    df["_home_location"] = df["_home_location"].str[1:-1]
    df[["lat", "lon"]] = df["_home_location"].str.split(",", 2, expand=True)
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    
    # Aggregate the number of enrollments at each lat/lon coordinate
    df["enrollments"] = 1
    df = df.groupby(["utility_code", "lat", "lon"]).sum().reset_index()
    
    # Subset out the desired columns
    df = df[["utility_code", "lat", "lon", "enrollments"]]

    # Rename the columns
    df.columns = ["Utility", "Latitude", "Longitude", "Enrollments"]
    
    return df


# Function for Utility Enrollment Map
def map(zoom, data, lat, lon, color):
    st.write(
        pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state={
                "latitude": lat,
                "longitude": lon,
                "zoom": zoom,
                "pitch": 0,
                "bearing": 0
            },
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data,
                    pickable=True,
                    opacity=0.5,
                    stroked=True,
                    filled=True,
                    radius_scale=10,
                    radius_min_pixels=1,
                    radius_max_pixels=100,
                    line_width_min_pixels=1,
                    get_position=["Longitude", "Latitude"],
                    get_radius="Enrollments",
                    get_fill_color=color,
                    get_line_color=[0, 0, 0]
                ),
            ],
        )
    )


# Filter the Data for a Specific Utility
@st.experimental_memo
def filterdata(df, utility):
    if utility == "DTE":
        data = df[df["Utility"] == "dte"].reset_index(drop=True)
    elif utility == "National Grid":
        data = df[df["Utility"] == "nationalgrid"].reset_index(drop=True)
    elif utility == "Xcel Energy":
        data = df[df["Utility"] == "xcel"].reset_index(drop=True)
    else:
        data = df
    return data

# Aggregate the Number of Enrollments
@st.experimental_memo
def countusers(data):
    data["Enrolled Users"] = 1
    data = data.groupby(["Utility"]).sum().reset_index()
    data = data[["Utility", "Enrolled Users"]]
    data.columns = ["Utility", "Enrolled Vehicles"]
    return data

# Aggregate the Number of Monthly Enrollments by Utilities
@st.experimental_memo
def monthlyusers():
    # Read in latest enrollment data from SDV team
    df = pd.read_csv("enrollments.csv")
    
    # Remove users that failed to enroll
    df = df[df["utility_status"] != "Failed"].reset_index(drop=True)
    
    # Get the enrollment month
    df["utility_status_date"] = pd.to_datetime(df["utility_status_date"], utc=True)
    df["month"] = df["utility_status_date"].dt.date
    df["month"] = df["month"].astype(str)
    df["month"] = df["month"].str[:7]
    
    # Subset desired columns
    df = df[["month", "utility_code"]]
    
    # Count number of enrollments
    df["Enrollments"] = 1
    df = df.groupby(["month", "utility_code"]).sum().reset_index()
    df["Enrollments"] = df["Enrollments"].astype(int)
    
    # Rename the columns
    df.columns = ["Month", "Utility", "Enrollments"]
    
    # Rename the utilities
    df.loc[df["Utility"] == "dte", "Utility"] = "DTE"
    df.loc[df["Utility"] == "nationalgrid", "Utility"] = "National Grid"
    df.loc[df["Utility"] == "xcel", "Utility"] = "Xcel Energy"
    
    return df

# Read in data for the number of enrolled vs not enrolled GM vehicles
@st.experimental_memo
def enrollments():
    # Read in total vehicular enrollments data
    df = pd.read_csv("total_vins.csv")
    
    return df

# Read in data for the number of enrolled vs not enrolled GM vehicles in the DTE service area
@st.experimental_memo
def enrollmentsDTE():
    # Read in total vehicular enrollments data
    df = pd.read_csv("vin_breakdown.csv")
    df = df[df['Utility'] == 'DTE'].reset_index(drop=True)
    
    return df

# Read in data for the number of enrolled vs not enrolled GM vehicles in the National Grid service area
@st.experimental_memo
def enrollmentsNGRID():
    # Read in total vehicular enrollments data
    df = pd.read_csv("vin_breakdown.csv")
    df = df[df['Utility'] == 'National Grid'].reset_index(drop=True)
    
    return df

# Read in data for the number of enrolled vs not enrolled GM vehicles in the XCEL service area
@st.experimental_memo
def enrollmentsXCEL():
    # Read in total vehicular enrollments data
    df = pd.read_csv("vin_breakdown.csv")
    df = df[df['Utility'] == 'Xcel Energy'].reset_index(drop=True)
    
    return df

# Read in data for average hourly cost of electricity for Xcel
def electricityRates():
    # Read in total vehicular enrollments data
    df = pd.read_csv("electricity_costs_xcel.csv")
    
    return df

# Create a Matplotlib bar chart of monthly enrollments
def barplot(df):

    # Create the axis and subplot
    fig, ax = plt.subplots(figsize=(10, 3))
    
    # Plot the monthly enrollment data
    df.plot(kind="bar", stacked=True, color=["#00FF00", "#FF0000", "#0000FF"], ax=ax)
    
    # Add the chart title
    plt.title("Monthly Vehicle Enrollments by Utility", fontsize=20)
    
    # Add axis titles
    plt.xlabel("Month", fontsize=15)
    plt.ylabel("Enrollments", fontsize=15)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    return fig

    
# Streamlit App Layout

# Title
st.title("""V1G Managed Charging Program""")

# App Summary
st.write(
    """
        Examine the distribution of GM BEVs/PHEVs enrolled in the V1G Managed Charging Program.
        Participants who elect to have their vehicle's charge times managed by General Motors received
        discounted electricity pricing rates.
    """
)

# Get Enrollment Data
data = load_data()

# See if there is a utility already selected
if not st.session_state.get("url_synced", False):
    try:
        utility = st.experimental_get_query_params()["utility"][0]
        st.session_state["utility"] = utility
        st.session_state["url_synced"] = True
    except KeyError:
        pass

# If the drop Down selection changes, update the query parameter
def update_query_params():
    utility_selected = st.session_state["utility"]
    st.experimental_set_query_params(utility=utility_selected)

st.header("""Vehicle Enrollments by Utility""")

# Layout the number of Rows/Columns for the next portion of the App
row1_1, row1_2 = st.columns((1, 3))

with row1_1:
    utility_selected = st.selectbox(
        "Select Utility", ("Show All", "DTE", "National Grid", "Xcel Energy")
    )
    st.header("""""")
    st.header("""""")
    st.header("""""")
    st.header("""""")
    st.header("""""")
    st.header("""""")
    st.write("Total Enrolled Vehicles by Utility")
    st.dataframe(countusers(data))

# Filter data by utility
if utility_selected == "DTE":
    with row1_2:
        map_data = filterdata(data, utility_selected)
        latitude = map_data["Latitude"].mean()
        longitude = map_data["Longitude"].mean()
        map(8, map_data, latitude, longitude, [0, 255, 0])
elif utility_selected == "National Grid":
    with row1_2:
        map_data = filterdata(data, utility_selected)
        latitude = map_data["Latitude"].mean()
        longitude = map_data["Longitude"].mean()
        map(8, map_data, latitude, longitude, [255, 0, 0])
elif utility_selected == "Xcel Energy":
    with row1_2:
        map_data = filterdata(data, utility_selected)
        latitude = map_data["Latitude"].mean()
        longitude = map_data["Longitude"].mean()
        map(8, map_data, latitude, longitude, [0, 0, 255])
else:
    with row1_2:
        latitude = data["Latitude"].mean()
        longitude = data["Longitude"].mean()
        map(3, data, latitude, longitude, [255,255,0])


# Layout the bar chart showing monthly enrollments by Utility
row2_1, row2_2 = st.columns((2, 3))

# Get the monthly enrollment data by utility
monthly_enrollments = monthlyusers()

with row2_1:
    st.header("""""")
    st.header("""""")
    st.header("""""")
    table_data = pd.pivot_table(monthly_enrollments, values="Enrollments", index="Month", columns="Utility", aggfunc=np.sum, fill_value=0)
    st.dataframe(table_data)

with row2_2:
    st.header("""""")
    st.header("""""")
    st.altair_chart(
        alt.Chart(monthly_enrollments, title="Monthly Vehicle Enrollments by Utility").mark_bar().encode(
            x="Month",
            y="sum(Enrollments)",
            tooltip=["Month", "Utility", "Enrollments"],
            color=alt.Color(field="Utility", type="nominal")
        ).properties(width=600)
    )

st.write(
    """
        DTE accounted for over 60% if enrolled vehicles despite only providing service to the greater Detroit, MI area.
        Many of the enrolled vehicles operating in the service areas covered by DTE are owned by GM employees. In its
        current pilot stage, vehicle owners must be invited by GM to participate in the program. As the program matures
        and moves out of the pilot stage, vehicle owners will be able to directly enroll with participating utilities.
    """
)

st.header("""Opportunities for Growth""")

# Layout the pie chart showing percentage of enrolled users vs number of GM EVs on the road
row3_1, row3_2, row3_3 = st.columns((2, 2, 2))

with row3_1:
    st.header("""""")
    st.altair_chart(
        alt.Chart(enrollmentsDTE(), title="GM Electric Vehicles Serviced by DTE Energy").mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Percent of Vehicles", type="quantitative"),
            color=alt.Color(field="Vehicle Status", type="nominal"),
            tooltip=["Utility", "Vehicle Status", "Percent of Vehicles", "Number of Vehicles"]
        )
    )

with row3_2:
    st.header("""""")
    st.altair_chart(
        alt.Chart(enrollmentsNGRID(), title="GM Electric Vehicles Serviced by National Grid").mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Percent of Vehicles", type="quantitative"),
            color=alt.Color(field="Vehicle Status", type="nominal"),
            tooltip=["Utility", "Vehicle Status", "Percent of Vehicles", "Number of Vehicles"]
        )
    )

with row3_3:
    st.header("""""")
    st.altair_chart(
        alt.Chart(enrollmentsXCEL(), title="GM Electric Vehicles Serviced by Xcel Energy").mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Percent of Vehicles", type="quantitative"),
            color=alt.Color(field="Vehicle Status", type="nominal"),
            tooltip=["Utility", "Vehicle Status", "Percent of Vehicles", "Number of Vehicles"]
        )
    )

# Layout the table explaining questions we've answered so far and questions we hope to answer as we gather more data
row4_1, row4_2 = st.columns((3, 3))

with row4_1:
    st.header("""Questions We have Answered with Current Data""")
    st.write("""• We know that the participation rate for vehicle owners invited into the program has been very high.""")
    st.write("""• We know the total number of enrolled vehicles operating in areas serviced by each participating utility.""")
    st.write("""• We know the total number GM BEVs/PHEVs operating in areas serviced by each participating utility.""")

with row4_2:
    st.header("""Questions We Want to Answer with More Data""")
    st.write("""• We want to know GM's overall market share of BEVs/PHEVs for service areas covered by each utility.""")
    st.write("""• We want to know which utility is providing service to each GM BEV/PHEV.""")
    st.write("""• We want to know if the participation rate will continue to remain high as we invite more participants into the program.""")
    st.write("""• We want to know the rate at which users opt-in/opt-out of their managed charging plans.""")
    st.write("""• We want to be able to tell utilities how much power is deferred from the grid during peak hours by enrolled vehicles.""")
    st.write("""• We want to be able to tell GM EV customers how much money they will be able to save on average by participating in the program.""")
    st.write("""• TBD""")
    
st.write (
    """
        The V1G Managed Charging Program is in its pilot stage. Currently, among the three utilities participating in the program,
        less than 5% of all GM electric vehicles operating in the service areas covered by these three utilities have been invited
        into the program. The vehicles that have not been invited are still undergoing a battery recall. Once these vehicles have
        had their batteries replaced, they will be invited into the program. This means there is exponential potential for growth
        as the program matures and moves beyond the pilot stage. Note, among vehicles invited into the program, we currently have
        a 100% participation rate from the vehicle owners.
    """
)

# Layout the row that show cases the average electriicty rates for Xcel for Enrolled and Non Enrolled Users

st.header("""Example Benefits of Enrolling in the Managed Charging Program""")
hover = alt.selection_single(
    fields=["Hour"],
    nearest=True,
    on="mouseover",
    empty="none",
)
st.altair_chart(
    alt.Chart(electricityRates(), title="Average Q2 (April - June) Xcel Energy Electricity Rates").mark_line(point="transparent").encode(
        x="Hour",
        y="Rate (¢/kWh)",
        color=alt.Color(field="Status", type="nominal"),
        tooltip=["Hour", "Status", "Rate (¢/kWh)"]
    ).properties(width=1000)
)

st.write("""• Participating Xcel Energy customers were charged an average 3.6 ¢/kWh for electricity.""")
st.write("""• Non Participating Xcel Energy customers were charged an average  8.3 ¢/kWh for electricity.""")
st.write("""• Participating Xcel Energy customers on average where charged 57% less for electricity.""")
st.write("""""")
st.write(
    """
        As we gather more data, we will be able to provide the same benefits analysis for all utilities participating in the
        managed charging program. We hope that the encouraging savings trend illustrated by Q2 Xcel Energy electricity rates
        will allow us to better advertise the program to more GM BEV/PHEV owners, and thus keep participation rates high for
        future vehicle owners invited into the program. We also hope that as we accumulate more and more participants, more
        and more utilites will see the benefits of providing incentives to BEV/PHEV owners in order to help offset electricity
        consumption rates during peak hours.
    """
)