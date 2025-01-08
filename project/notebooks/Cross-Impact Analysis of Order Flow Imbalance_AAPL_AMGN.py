# -*- coding: utf-8 -*-
"""Work_Trial_Task_Final.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1r5-r5FT5MHrKCFOU_qZ7KqnhkpGhPszq
"""

# pip install databento

"""This notebook provides a comprehensive framework for analyzing the cross-impact of Order Flow Imbalance (OFI) in equity markets. It implements step-by-step methodologies for data preparation, feature engineering, modeling, and visualization to study both contemporaneous and predictive relationships between OFIs and stock price changes. The notebook is structured around key functions that encapsulate specific tasks, enabling modular and reusable workflows.

**Key Functions and Their Purposes**

1. **stocks_imported**: Dynamically imports and cleans stock data.



2. **compute_multilevel_ofi**: Calculates multi-level OFIs for the top 5 levels of the limit order book.

3. **apply_pca_to_ofis**: Integrates multi-level OFIs into a single variable using PCA to reduce dimensionality.

4. **resample_integrated_ofis**: Resamples data to a uniform frequency (e.g., 1-minute intervals) and aligns timestamps across stocks.

5. **calculate_returns**: Computes logarithmic returns and future returns over specified horizons (e.g., 1-minute, 5-minute).

6. **assess_contemporaneous_self_vs_cross_impact**: Evaluates the contemporaneous explanatory power of self-impact vs. cross-impact using LASSO regression.

7. **assess_predictive_self_vs_cross_impact**: Analyzes the predictive power of lagged self vs. cross-asset OFIs on future returns.

8. **Visualization**:
Heatmaps, scatter plots, and bar plots are used to illustrate cross-impact relationships, coefficient magnitudes, and model performance metrics.

9. **summarize_impact**: Summarizes model performance metrics  for both
contemporaneous and predictive models across multiple stocks and horizons.
"""

import warnings
from sklearn.decomposition import PCA
import pandas as pd
warnings.filterwarnings('ignore')
from sklearn.linear_model import LassoCV
from sklearn.metrics import r2_score
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

stocks = ["AAPL", "AMGN", "TSLA", "JPM", "XOM"]
count=0

#this dictionary will store the imported stocks, name of the stock as key and the dataframe as the value
stocks_imported={}

#for loop to import all the stock's dataframes
for stock in stocks:
  globals()[stock.lower()]= pd.read_csv(f'/content/drive/MyDrive/Anshul/Blockhouse/{stock}_filtered_data_cleaned.csv')
  count+=1
  stocks_imported[stock]=globals()[stock.lower()]
  if count==2:    #considering only first to stocks due to memory limitations
    break

#In this for loop, I have dropped the duplicates from the timestamp column and set it as the index and also sorting the column
for stock,df in stocks_imported.items():
  df=df.drop_duplicates(subset='ts_event')
  df['ts_event'] = pd.to_datetime(df['ts_event'])

  df = df.sort_values(by='ts_event')  # Ensuring data is sorted by timestamp

  df.set_index('ts_event', inplace=True)  # Settting timestamp as index

  stocks_imported[stock] = df

#In this function I am calculating OFI's for the first 5 levels

def compute_multilevel_ofi(stocks):

    #creating a dictionary to store every stock's dataframe that will consist the columns having OFIs as per levels
    df_ofi_stock = {}

    for stock, df in stocks.items():
        df_ofi = pd.DataFrame(index=df.index)

        #Compute OFI for each level(top 5 levels)
        for level in range(5):
            bid_px_col = f'bid_px_0{level}'
            ask_px_col = f'ask_px_0{level}'
            bid_sz_col = f'bid_sz_0{level}'
            ask_sz_col = f'ask_sz_0{level}'

            delta_bid_px = df[bid_px_col].diff()
            delta_ask_px = df[ask_px_col].diff()
            delta_bid_sz = df[bid_sz_col].diff()
            delta_ask_sz = df[ask_sz_col].diff()

            # Calculate OFI at this level
            df_ofi[f'ofi_{level}'] = (
                (delta_bid_sz * delta_bid_px) -
                (delta_ask_sz * delta_ask_px)
            )

        # Drop NaN values
        df_ofi.dropna(inplace=True)

        #Adding a mid_price column to calculate returns
        df_ofi['mid_price']=(df['bid_px_00']+df['ask_sz_00'])/2
        df_ofi_stock[stock] = df_ofi

    return df_ofi_stock

# Compute multi-level OFIs
df_ofi_stock = compute_multilevel_ofi(stocks_imported)

#In this function I am implementing dimensionality reduction through Principal Component Analysis, integrating the OFIs into a single column
def apply_pca_to_ofis(df_ofi_stock):
    df_ofi_stock_pca = {}
    for stock, df in df_ofi_stock.items():

        ofi_columns = [col for col in df.columns if 'ofi_' in col]  #get all the OFI columns

        # Apply PCA to multi-level OFIs
        pca = PCA(n_components=1)
        integrated_ofi = pca.fit_transform(df[ofi_columns])

        # Add integrated OFI to the DataFrame
        df['integrated_ofi'] = integrated_ofi
        df_ofi_stock_pca[stock] = df

    return df_ofi_stock_pca

# Apply PCA on multi-level OFIs
df_ofi_stock_pca = apply_pca_to_ofis(df_ofi_stock)

'''
    In this function, I have resampled the timestamp to a 1 minute frequency and set a unified index for all stock's dataframes to ensure that
    the self and cross impacts are calculated smoothly
'''

def resample_integrated_ofis(df_ofi_stock_pca, freq='1T'):

    #Create a dictionary to store all the resampled dataframes of all the stocks
    resampled_stocks = {}
    unified_index = None

    for stock, df in df_ofi_stock_pca.items():
        resampled_stocks[stock] = df.resample(freq).mean()  # Resample to desired frequency
        if unified_index is None:
                unified_index = resampled_stocks[stock].index
        else:
            unified_index = unified_index.union(resampled_stocks[stock].index)

    # Step 2: Align all DataFrames to the unified index
    for stock in resampled_stocks.keys():
        resampled_stocks[stock] = resampled_stocks[stock].reindex(unified_index)
    return resampled_stocks

# Resample integrated OFIs to 1-minute bins
resampled_pca_stocks = resample_integrated_ofis(df_ofi_stock_pca)

#In this function I am filling all the NaN values by the mean of the column
def fill_null_values(resampled_pca_stocks):

  #creating a dictionary to store all the stock's updated dataframes
  resampled_pca_stocks_filled={}

  for stock,df in resampled_pca_stocks.items():
    for col in df.columns:
      df[col]=df[col].fillna(df[col].mean())    #replacing all the NaN values with the column's mean

    resampled_pca_stocks_filled[stock]=df
  return resampled_pca_stocks_filled

resampled_pca_stocks_filled=fill_null_values(resampled_pca_stocks)

'''
    In this function I am calculating the returns and future returns, I have used two horizons, 1 minute and 5 minute
'''
def calculate_returns(resampled_pca_stocks_filled,method='ffill',horizons=[1,5]):
    resampled_stocks=resampled_pca_stocks_filled

    for stock, df in resampled_stocks.items():
        mid_price = df['mid_price']

        # Calculate logarithmic returns
        resampled_stocks[stock]['returns'] = np.log(mid_price / mid_price.shift(1))
        resampled_stocks[stock]['returns'].fillna(method='bfill',inplace=True)  #fill the NaN values

        #Calculate logarithmic future returns
        for h in horizons:
          resampled_stocks[stock][f'future_return_{h}'] = np.log(df['mid_price'].shift(-h) / df['mid_price'])

        resampled_stocks[stock].fillna(method=method,inplace=True)    #fill NaN values

    return resampled_pca_stocks_filled

# Calculate returns after resampling datasets
resampled_pca_ofis_returns = calculate_returns(resampled_pca_stocks_filled)

'''
    In this function I have calculated the contemporaneous self and cross impact of OFI's
    I have used LASSO regression model for sparsity

'''

def assess_contemporaneous_self_vs_cross_impact(df_ofi_stock_pca):
    results = {}
    for stock, df in df_ofi_stock_pca.items():

        # Self-impact: Using the stock's own integrated OFI
        X_self = df[['integrated_ofi']].values
        y = df['returns'].values

        # Cross-impact: Using integrated OFIs from all other stocks
        X_cross = pd.concat(
            [df_other['integrated_ofi'] for s, df_other in df_ofi_stock_pca.items() if s != stock], axis=1
        ).values

        # Fitting separate LASSO models for self and cross impacts
        lasso_self = LassoCV(cv=5).fit(X_self, y)
        lasso_cross = LassoCV(cv=5).fit(X_cross, y)

        results[stock] = {
            'self_coefficients': lasso_self.coef_,
            'self_intercept': lasso_self.intercept_,
            'self_R2': lasso_self.score(X_self, y),
            'cross_coefficients': lasso_cross.coef_,
            'cross_intercept': lasso_cross.intercept_,
            'cross_R2': lasso_cross.score(X_cross, y),
        }
    return results

#getting the results
contemporaneous_results = assess_contemporaneous_self_vs_cross_impact(resampled_pca_ofis_returns)

contemporaneous_results

def create_lagged_features(df_ofi_stock_pca, lags):
    """
    In this function I have created lagged features for integrated OFIs.
    Value of lags used is [1,5]

    """

    #using a dictionary to store the lagged features
    lagged_features = {}

    for stock, df in df_ofi_stock_pca.items():
        lagged_df = df[['integrated_ofi']].copy()
        for lag in lags:

            #Adding columns as per lag values
            lagged_df[f'integrated_ofi_lag_{lag}'] = df['integrated_ofi'].shift(lag)
            lagged_df[f'future_return_{lag}']=df[f'future_return_{lag}']
            lagged_features[stock] = lagged_df.dropna()  # Drop rows with NaN values due to shifting

    return lagged_features

lags = [1, 5]  # Define lags
lagged_features = create_lagged_features(resampled_pca_ofis_returns, lags)

'''
    In this function I have calculated the predicted self and cross impact analysis

'''

def assess_predictive_self_vs_cross_impact(lagged_features, future_returns_column):
    results = {}
    for stock, df in lagged_features.items():

        # Self-lagged impact: Use only lagged OFIs from the same stock
        X_self = df[[col for col in df.columns if 'lag' in col]].values
        y = df[future_returns_column].values

        # Cross-lagged impact: Use lagged OFIs from all other stocks
        X_cross = pd.concat(
            [df_other[[col for col in df_other.columns if 'lag' in col]]
             for s, df_other in lagged_features.items() if s != stock], axis=1
        ).values

        # Fit separate LASSO models for self and cross impacts
        lasso_self = LassoCV(cv=5).fit(X_self, y)
        lasso_cross = LassoCV(cv=5).fit(X_cross, y)

        results[stock] = {
            'self_coefficients': lasso_self.coef_,
            'self_intercept': lasso_self.intercept_,
            'self_R2': lasso_self.score(X_self, y),
            'cross_coefficients': lasso_cross.coef_,
            'cross_intercept': lasso_cross.intercept_,
            'cross_R2': lasso_cross.score(X_cross, y),
        }
    return results

# Run the assessment for 1-minute horizon
predictive_results_1 = assess_predictive_self_vs_cross_impact(lagged_features, 'future_return_1')

# Run the assessment for 5-minute horizon
predictive_results_5 = assess_predictive_self_vs_cross_impact(lagged_features, 'future_return_5')

predictive_results_5

predictive_results_1

def summarize_impact(results):
    summary = []
    for stock, res in results.items():
        summary.append({
            'stock': stock,
            'self_R2': res['self_R2'],
            'cross_R2': res['cross_R2'],
            'self_avg_coeff': abs(res['self_coefficients']).mean(),
            'cross_avg_coeff': abs(res['cross_coefficients']).mean(),
        })
    return pd.DataFrame(summary)

# Summarize contemporaneous results
summary_contemporaneous = summarize_impact(contemporaneous_results)

# Summarize predictive results (e.g., 1-minute horizon)
summary_predictive_1 = summarize_impact(predictive_results_1)

# Summarize predictive results (e.g., 5-minute horizon)
summary_predictive_5 = summarize_impact(predictive_results_5)

print("Contemporaneous Results:")
print(summary_contemporaneous)

print("Predictive Results (1-Minute Horizon):")
print(summary_predictive_1)

print("Predictive Results (5-Minute Horizon):")
print(summary_predictive_5)

# Data for heatmap
heatmap_data = {
    "Self-Impact (Contemporaneous)": [0.000383, 0.000000],
    "Cross-Impact (Contemporaneous)": [0.000000, 0.000087],
    "Self-Impact (1-Minute Predictive)": [0.0, 0.0],
    "Cross-Impact (1-Minute Predictive)": [0.000002, 0.000084],
    "Self-Impact (5-Minute Predictive)": [1.952582e-04, 1.109858e-22],
    "Cross-Impact (5-Minute Predictive)": [1.788928e-06, 1.098453e-19]
}

# Convert to DataFrame
heatmap_df = pd.DataFrame(heatmap_data, index=["AAPL", "AMGN"])

# Create heatmap
plt.figure(figsize=(10, 6))
sns.heatmap(heatmap_df, annot=True, fmt=".2e", cmap="coolwarm", cbar_kws={'label': 'Coefficient Magnitude'})
plt.title("Heatmap of Self vs Cross Impact Coefficients")
plt.ylabel("Stock")
plt.xlabel("Model Type")
plt.xticks(rotation=45)
plt.show()

# Data for scatter plot
scatter_data = {
    "Model": ["Contemporaneous", "1-Minute Predictive", "5-Minute Predictive"],
    "Self-R2 (AAPL)": [0.001201, 0.0, 0.000539],
    "Cross-R2 (AAPL)": [0.000000, 0.000103, 0.000078],
    "Self-R2 (AMGN)": [0.000000, 0.0, 0.000000],
    "Cross-R2 (AMGN)": [0.000236, 0.000461, 0.000000]
}

# Convert to DataFrame
scatter_df = pd.DataFrame(scatter_data)

# Plot R^2 comparison for AAPL
plt.figure(figsize=(8, 6))
plt.scatter(scatter_df["Model"], scatter_df["Self-R2 (AAPL)"], label="Self-R2 (AAPL)", color="blue")
plt.scatter(scatter_df["Model"], scatter_df["Cross-R2 (AAPL)"], label="Cross-R2 (AAPL)", color="orange")
plt.title("Explanatory Power (R^2) Comparison for AAPL")
plt.ylabel("(R^2)")
plt.xlabel("Model Type")
plt.legend()
plt.show()

# Plot R^2 comparison for AMGN
plt.figure(figsize=(8, 6))
plt.scatter(scatter_df["Model"], scatter_df["Self-R2 (AMGN)"], label="Self-R2 (AMGN)", color="green")
plt.scatter(scatter_df["Model"], scatter_df["Cross-R2 (AMGN)"], label="Cross-R2 (AMGN)", color="red")
plt.title("Explanatory Power (R^2) Comparison for AMGN")
plt.ylabel("R^2")
plt.xlabel("Model Type")
plt.legend()
plt.show()
