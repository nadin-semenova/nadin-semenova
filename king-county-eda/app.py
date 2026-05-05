import streamlit as st

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from datetime import datetime, date, time, timedelta
from matplotlib.dates import DateFormatter, MonthLocator

plt.style.use('bmh')

url = 'https://www.kaggle.com/datasets/harlfoxem/housesalesprediction'

st.title('EDA: KING COUNTY HOME SALES')
st.markdown('**Data source:** [House Sales in King County, USA](%s)' % url)

st.markdown('**Time span:** May 2014 – May 2015')

#=====================================================================================================
## 1. Overview of the data
st.write( '### 1. Dataset Preview ')
df = pd.read_csv('data/King_country_house_clean_all_ohheNaN.csv')
st.dataframe(df, use_container_width=True)
#=====================================================================================================
## 2. Describtion
st.write( '### 2. Data Statistics ')
st.write(df.describe())

#=====================================================================================================
## 3. Correlation matrix
st.write( '### 3. Correlation matrix')
selected_columns = ['price', 'bedrooms_num', 'bathrooms_num', 'sqft_living', 'sqft_lot','floors_total','waterfront','view','condition','grade','lat','long','sqft_lot15']
correlation_matrix = df[selected_columns].corr()


fig = plt.figure(figsize=(8, 6))
sns.heatmap(correlation_matrix, 
            annot=True,
            fmt=".2f",
            cmap="coolwarm",
            square=True,
            linewidths=0.5,
            cbar_kws={"shrink": 0.8})

plt.title("Correlation matrix for selected columns", fontsize=16, pad=20)
plt.xticks(fontsize=12, rotation=45, ha="right")
plt.yticks(fontsize=12)
st.pyplot(fig)

#=====================================================================================================
## 4. Relationships in data
st.write( '### 4. Relationships in data')
fig = plt.figure(figsize=(6,4))
plt.hist(df['price']/ 1000000, bins= 50, edgecolor='w',color='blue')
plt.title('Price distribution', fontsize=15)
plt.xlabel('Price $\\times 10^6$, USD', fontsize=12)
plt.ylabel('Frequency', fontsize=12)

plt.xlim(0.08, 3.5)
plt.ylim(0, 7000)

plt.gca().set_facecolor('white')
plt.gcf().set_facecolor("white")

plt.gca().spines['left'].set_color("black")
plt.gca().spines['left'].set_linewidth(1.5)
plt.gca().spines['bottom'].set_color("black")
plt.gca().spines['bottom'].set_linewidth(1.5)

st.pyplot(fig)

#=====================================================================================================
## 5. Research questions and hypothesis
st.write( '### 5. Research questions and hypothesis')

st.write( '#### Hypothesis 1: The peak in demand')


def get_season(month):
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Autumn'

df['season'] = df['month'].apply(get_season)

seasonal_sales = df.groupby('season').size().reindex(['Winter', 'Spring', 'Summer', 'Autumn'])

fig = plt.figure(figsize=(6, 4))
sns.barplot(x=seasonal_sales.index, y=seasonal_sales.values, color="skyblue")
plt.title("Number of sales per season from May 2014 to May 2015", pad=20)
plt.xlabel("Season" , labelpad=15)
plt.ylabel("Number of Sales", labelpad=15)
plt.gca().set_facecolor("white")
plt.gcf().set_facecolor("white")
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.gca().spines['left'].set_color("black")
plt.gca().spines['left'].set_linewidth(1.5)
plt.gca().spines['bottom'].set_color("black")
plt.gca().spines['bottom'].set_linewidth(1.5)
plt.ylim(0, 10000)
plt.xlim(-0.4, 3.4)
st.pyplot(fig)

st.write('Houses sold in November and December have higher average prices than those in January and February, possibly due to seasonal changes in demand and fewer available houses at the end of the year.')
#=====================================================================================================

st.write( '#### Hypothesis 2: Higher averange prices')
monthly_stats = df.groupby('month')['price'].agg(['mean', 'median']).rename(columns={'mean': 'Average Price', 'median': 'Median Price'})

fig = plt.figure(figsize=(6, 4))

plt.gcf().set_facecolor("white")

plt.plot(monthly_stats.index, monthly_stats['Average Price']/100000, marker='o', color='b', label='Average Price',zorder=5)
plt.plot(monthly_stats.index, monthly_stats['Median Price']/100000, marker='s', linestyle='--', color='g', label='Median Price',zorder=5)

plt.xlim(1, 12)
plt.ylim(0, 8)

plt.xlabel("Month",labelpad=15)
plt.ylabel("Price $\\times 10^5$, USD")
plt.title("Average and Median Housing Prices by Month",pad=20)
plt.xticks(ticks=range(1, 13), labels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
plt.grid(axis='y', linestyle='--', alpha=0.7)

yticks = plt.yticks()[0]
yticks = yticks[yticks != 0]
plt.yticks(yticks)

plt.legend()
plt.gca().set_facecolor("white")

st.pyplot(fig)

#=====================================================================================================

st.write( '#### Hypothesis 3: Higher prices in the north')
st.write('Distribution based on the median latitude: properties located above or below or the median latitude. Horizontal line - North-South boundary.')
median_latitude = df['lat'].median()
df['region'] = np.where(df['lat'] > median_latitude, 'North', 'South')

fig = plt.figure(figsize=(10, 8))

colors = {'North': 'lightblue', 'South': 'lightcoral'}

for region, color in colors.items():
    subset = df[df['region'] == region]
    plt.scatter(subset['long'], subset['lat'], 
                color=color, alpha=0.5, s=20, label=f'{region} Region')

median_latitude = df['lat'].median()
plt.axhline(median_latitude, color='gray', linestyle='--', linewidth=1.5, label='North-South Divider')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Geographic Distribution of Home Prices by Region')
plt.legend(title='Region')

st.pyplot(fig)

df['price_per_sqft'] = df['price'] / df['sqft_living']

median_latitude = df['lat'].median()
df['region'] = np.where(df['lat'] > median_latitude, 'North', 'South')

region_sqft_means = df.groupby('region')['price_per_sqft'].mean()

colors = {'North': '#ADD8E6', 'South': '#F08080'}

y_min = df['price_per_sqft'].min()
y_max = df['price_per_sqft'].max()

fig = plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
sns.barplot(
    x=region_sqft_means.index, 
    y=region_sqft_means.values, 
    hue=region_sqft_means.index,
    palette=colors,
    order=['North', 'South']
)
plt.ylim(0, y_max)
plt.title("Average price per 1 ft² by region")
plt.xlabel("Region", fontsize=14)
plt.ylabel("Price per 1 ft², USD", fontsize=14)
plt.xticks(fontsize=12)
plt.gca().set_facecolor("white")

plt.subplot(1, 2, 2)
sns.boxplot(x='region', y='price_per_sqft', data=df, hue='region', palette=colors, order=['North', 'South'])
plt.ylim(0, y_max)
plt.title("Price per 1 ft² distribution by region")
plt.xlabel("Region", fontsize=14)
plt.ylabel("Price per 1 ft², USD", fontsize=14)
plt.xticks(fontsize=12)
plt.gca().set_facecolor("white")

plt.tight_layout()
st.pyplot(fig)


grade_distribution = df.groupby(['grade', 'region']).size().unstack().fillna(0)
grade_distribution = grade_distribution.div(grade_distribution.sum(axis=0), axis=1) * 100

max_value = 100

fig, ax = plt.subplots(figsize=(8, 5))

palette = {'North': 'lightblue', 'South': 'lightcoral'}

grade_distribution.plot(kind='bar', color=[palette['North'], palette['South']], ax=ax)
plt.title("Distribution of Grade by Region", fontsize=14)
plt.xlabel("Grade", fontsize=14)
plt.ylabel("%", fontsize=14)
plt.legend(title='Region', fontsize=14)
plt.tick_params(axis='x', rotation=0, labelsize=14)
plt.tick_params(axis='y', labelsize=14)
plt.ylim(0, max_value)

st.pyplot(fig)

#=====================================================================================================

st.write('#### 6. CLIENT: Larry Sanders — Buyer')
st.write('Requirements: waterfront · limited budget · large neighbouring lots · 2–3 bedrooms · close to downtown Seattle')

lat_center = 47.606
long_center = -122.33

df_waterfront = df[df['waterfront'] == 1]
df_budget_friendly = df_waterfront[df_waterfront['price'] <= df_waterfront['price'].median()]
df_large_lots = df_budget_friendly[df_budget_friendly['sqft_lot15'] >= df_budget_friendly['sqft_lot15'].quantile(0.75)]
df_fewer_children = df_large_lots[(df_large_lots['bedrooms_num'] >= 2) & (df_large_lots['bedrooms_num'] <= 3)]

df_fewer_children = df_fewer_children.copy()
df_fewer_children['distance_to_center'] = np.sqrt(
    ((df_fewer_children['lat'] - lat_center) * 111) ** 2 + 
    ((df_fewer_children['long'] - long_center) * 85) ** 2
)

median_distance = df_fewer_children['distance_to_center'].median()
df_central = df_fewer_children[df_fewer_children['distance_to_center'] <= median_distance].copy()

st.write(f'**{len(df_central)} properties** matched all 5 filters.')

# Weighted score: price 35%, distance 35%, privacy (sqft_lot15) 15%, area (sqft_living) 15%
df_central['score'] = (
    (1 - (df_central['price'] - df_central['price'].min()) / (df_central['price'].max() - df_central['price'].min())) * 0.35 +
    (1 - (df_central['distance_to_center'] - df_central['distance_to_center'].min()) / (df_central['distance_to_center'].max() - df_central['distance_to_center'].min())) * 0.35 +
    ((df_central['sqft_lot15'] - df_central['sqft_lot15'].min()) / (df_central['sqft_lot15'].max() - df_central['sqft_lot15'].min())) * 0.15 +
    ((df_central['sqft_living'] - df_central['sqft_living'].min()) / (df_central['sqft_living'].max() - df_central['sqft_living'].min())) * 0.15
)

df_top = df_central.sort_values('score', ascending=False).head(8)

display_cols = {
    'house_id': 'ID',
    'price': 'Price ($)',
    'sqft_living': 'Living Area (sqft)',
    'bedrooms_num': 'Bedrooms',
    'distance_to_center': 'Distance to Center (km)',
    'sqft_lot15': 'Neighbour Lot (sqft)',
    'score': 'Score'
}

df_display = df_top[list(display_cols.keys())].rename(columns=display_cols).reset_index(drop=True)
df_display['Price ($)'] = df_display['Price ($)'].apply(lambda x: f"${x:,.0f}")
df_display['Distance to Center (km)'] = df_display['Distance to Center (km)'].round(1)
df_display['Score'] = df_display['Score'].round(3)

st.dataframe(df_display, use_container_width=True)
