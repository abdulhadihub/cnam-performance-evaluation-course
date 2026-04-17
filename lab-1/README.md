# Performance Evaluation - Lab 1: Random Variables

This project generates random samples from various probability distributions and creates histograms for visualization and analysis.

## Project Overview

This lab includes two main Python scripts:

1. **`random_generator.py`** - Generates random samples from 5 different probability distributions
2. **`plot_histograms.py`** - Creates and saves histograms from the generated data

### Distributions Generated

The project generates samples from the following distributions:

- **Uniform (Integer)**: Values between 90-110
- **Uniform (Double)**: Values between 10.0-12.0
- **Normal**: Mean = 15, Standard Deviation = 3
- **Exponential**: Mean = 0.05
- **Lognormal**: Mean (log) = 2.0, SD (log) = 1.0

### Sample Sizes

Each distribution is generated with 4 different sample sizes:
- n = 10
- n = 100
- n = 1,000
- n = 10,000

This results in **20 data files** and **20 histogram PNG files** in total.

## Project Structure

```
lab-1/
├── code/
│   ├── random_generator.py      # Generates random samples
│   └── plot_histograms.py       # Creates histograms
├── plots/
│   ├── [distribution]-[n].txt   # Raw data files
│   └── [distribution]-[n].png   # Histogram images
├── reports/
│   └── lab-random-variables.tex # LaTeX report
└── README.md                     # This file
```

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip or uv package manager

### Install Dependencies

Using pip:
```bash
pip install numpy matplotlib scipy
```

Or using uv (if you have it installed):
```bash
uv pip install numpy matplotlib scipy
```

## How to Run

### Step 1: Generate Random Samples

Run the random variable generator to create data files:

```bash
python code/random_generator.py
```

**Output**: This will generate 20 data files in the `plots/` directory with names like:
- `uniform-int-10.txt`, `uniform-int-100.txt`, etc.
- `uniform-double-10.txt`, `uniform-double-100.txt`, etc.
- `normal-10.txt`, `normal-100.txt`, etc.
- `exponential-10.txt`, `exponential-100.txt`, etc.
- `lognormal-10.txt`, `lognormal-100.txt`, etc.

The script will also print descriptive statistics for each distribution to the console.

### Step 2: Generate Histograms

Run the histogram generator to create visualizations:

```bash
python code/plot_histograms.py
```

**Output**: This will generate 20 PNG histogram files in the `plots/` directory with the same naming pattern as the data files (e.g., `uniform-int-10.png`, `normal-100.png`, etc.).

Each histogram includes:
- Distribution name and sample size in the title
- Frequency bars with Sturges' binning algorithm
- Statistical annotations (n, μ, σ) in the top-right corner

## Notes

- The random seed is fixed (SEED = 10) to ensure reproducible results across runs
- Statistics are computed using NumPy functions with Bessel's correction (ddof=1) for unbiased sample variance
- Histograms use Sturges' binning rule for automatic bin calculation

## Dependencies

- **numpy**: Numerical computing library for data generation and statistics
- **matplotlib**: Plotting library for creating histograms
- **scipy**: Scientific computing (optional, for additional statistical functions)

## License

This is a lab assignment for CNAM.

## Author

Group 10 - Performance Evaluation Lab
Abdul Hadi Farooq
Ali Raza
Ali Haider
