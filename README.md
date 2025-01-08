#  Overview
This project provides a comprehensive framework to analyze the cross-impact of Order Flow Imbalance (OFI) across multiple stocks, focusing on both contemporaneous and predictive relationships with short-term price returns. 
The repository is structured to facilitate modular code development, reproducibility of results, and clarity in analysis workflows.

## Getting Started
### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Clone the Repository
```bash
git clone https://github.com/yourusername/Order-Flow_Imbalance.git
cd ofi-crossimpact
```

### Install the required packages

   ```bash
   pip install -r requirements.txt
   ```

### Calculating OFIs, implementing PCA and analysing Self and Cross Impact analysis

1. **Navigate to the Notebooks directory:**

   ```bash
   cd project/notebooks
   ```

2. **Launch Jupyter Notebook:**

   ```bash
   jupyter notebook
   ```

3. Open the notebook for the respective stocks and run the cells.
4. Import all the stocks CSV's by running 'Data_import.ipynb', it will generate CSV files
5. Download these files and provide the path to the CSV files in the 'OFI_calculation.ipynb' notebook
6. Because of memory restrictions I have grouped the stocks into different notebooks, if you want to consider all the stocks at once, remove the break statement from the cell that imports the respective stock's CSV file.


##  Summary of Findings
-  Contemporaneous Impact Analysis:
1.  For AAPL, self-impact shows higher explanatory power (R² = 0.001201) compared to cross-impact (R² = 0.000000), with a self-impact coefficient of 0.0003831
2.  For AMGN, cross-impact dominates (R² = 0.000236) over self-impact (R² = 0.000000), with a cross-impact coefficient of 0.000087
   
-  Predictive Cross-Impact:
1.  At 1-minute horizon:
-  Both stocks show zero self-impact (R² = 0.000)
-  Cross-impact provides marginal predictive power for both AMGN (R² = 0.000461) and AAPL (R² = 0.000103)1
2.  At 5-minute horizon:
-  AAPL shows weak self-impact (R² = 0.000539) and minimal cross-impact (R² = 0.000078)
-  AMGN shows negligible impact for both self and cross terms (R² ≈ 0)

###  Key Insights
1.  Coefficient Magnitudes:
-  The heatmap reveals that self-impact coefficients are generally larger than cross-impact coefficients
-  Coefficient magnitudes decay rapidly over longer horizons
  
2. Temporal Decay:
-  Both self and cross-impact effects weaken significantly at longer horizons (5-minute vs 1-minute)
-  Cross-impact provides better predictive power at shorter horizons
  
3.  Asymmetric Effects:
-  AAPL and AMGN show different patterns of self vs cross-impact
-  AMGN appears more susceptible to cross-impact effects in contemporaneous analysis1

These findings suggest that while OFI cross-impact exists, its explanatory and predictive power is relatively weak and decays rapidly over time. 
The analysis indicates that market participants should focus on shorter-term horizons when considering cross-asset OFI signals for trading strategies.

