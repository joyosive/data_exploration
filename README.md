# Overview
This repository contains a comprehensive data analysis project focusing on DeFi swap transactions and smart contract event logs.

## Project Structure

```
data_exploration/
├── README.md                        # Project documentation
├── task1_sql/                       # SQL Revenue Analysis
│   ├── final_revenue_query.sql      # Main revenue calculation query
│   └── task1_revenue_analysis.md    # Detailed insights & recommendations
└── task2_python/                    # Python Data Processing
    ├── event_analysis.py            # Core analysis module
    ├── run_analysis.py              # Main execution script
    ├── contract_events.csv          # Dataset (20k records)
    ├── event_type_frequency.png     # Visualization output
    ├── TASK2_ANALYSIS.md            # Detailed approach & assumptions
    └── pyproject.toml               # Project dependencies
```

## Task 1: DeFi Transaction Revenue Analysis

### Overview
Analysis of swap transactions to calculate revenue based on tiered fee structures.

### Key Features
- Complex tiered fee calculation based on swap volume
- Protocol-specific fee logic implementation
- Revenue optimization recommendations
- Total Revenue Calculated: **$276,084.43**

### Query Results
- **Total Transactions**: 21,317
- **Total Volume**: $240,630,552.01
- **Average Revenue per Transaction**: $13.16
- **Overall Revenue Rate**: 0.1147%
- **Revenue Breakdown**:
  - CoW SafeApp: $17,692.25
  - 1inch SafeApp: $42,273.99
  - KyberSwap: $3,646.58
  - Native Swaps: $212,471.62
    - Stablecoin: $11,597.47
    - Non-Stablecoin: $200,874.15

### Usage
Execute the SQL query in `task1_sql/final_revenue_query.sql` in Dune Query Engine.

## Task 2: Smart Contract Event Analysis

### Overview
Analysis of ~20,000 blockchain event logs to identify patterns, anomalies, and derive operational insights.

**Technologies**: Built with pandas for data manipulation and uv for modern Python package management.

### Setup & Installation

#### Required: Using uv package manager
This project uses **uv** for fast, reliable Python package management.

```bash
# Install uv first (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Then run
cd task2_python
uv sync
uv run python run_analysis.py
```

### Key Results
- **433 orphan events** detected (2.16% of dataset)
- **~75 seconds** average interval between contract events  
- **5 bot addresses** identified with coordinated behavior
- **Data quality issues** found and documented

**Detailed analysis**: See `task2_python/task2_analysis.md` for complete methodology, assumptions, & technical implementation details.

## Requirements

- Python 3.11+
- pandas >= 2.0.0
- numpy >= 1.24.0
- matplotlib >= 3.7.0
- uv (package manager)

## Submission Checklist

**Dune Query**: `task1_sql/final_revenue_query.sql` - Revenue calculation with given fee structure
**Code**: Clean, modular Python analysis 
**Visualizations**: Event type frequency charts in `task2_python/event_type_frequency.png`
**Analysis Artifacts**: 
  - `task1_sql/task1_revenue_analysis.md` - Strategic insights and recommendations
  - `task2_python/task2_analysis.md` - Technical approach and assumptions
**README**: Setup and execution instructions 
