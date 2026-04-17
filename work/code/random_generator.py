import numpy as np
import statistics
import os

SEED = 10

UNIFORM_INT_MIN = 90
UNIFORM_INT_MAX = 110

UNIFORM_DOUBLE_MIN = 10.0
UNIFORM_DOUBLE_MAX = 12.0

NORMAL_MEAN = 15
NORMAL_STDEV = 3

EXPONENTIAL_MEAN = 0.05

LOGNORMAL_MEANLOG = 2.0
LOGNORMAL_SDLOG = 1.0

SAMPLE_SIZES = [10, 100, 1000, 10000]

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'plots')


def generate_uniform_int(n):
    """Generate n integers uniformly distributed in [90, 110]."""
    return np.random.uniform(UNIFORM_INT_MIN, UNIFORM_INT_MAX + 1, n).astype(int)


def generate_uniform_double(n):
    """Generate n doubles uniformly distributed in [10.0, 12.0]."""
    return np.random.uniform(UNIFORM_DOUBLE_MIN, UNIFORM_DOUBLE_MAX, n)


def generate_normal(n):
    """Generate n values from Normal distribution (mean=15, stdev=3)."""
    return np.random.normal(NORMAL_MEAN, NORMAL_STDEV, n)


def generate_exponential(n):
    """Generate n values from Exponential distribution (mean=0.05)."""
    return np.random.exponential(EXPONENTIAL_MEAN, n)


def generate_lognormal(n):
    """Generate n values from Lognormal distribution (meanlog=2.0, sdlog=1.0)."""
    return np.random.lognormal(LOGNORMAL_MEANLOG, LOGNORMAL_SDLOG, n)


def compute_statistics(data):
    """Compute descriptive statistics for a data array."""
    return {
        'count': len(data),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'mean': float(np.mean(data)),
        'variance': float(np.var(data, ddof=1)) if len(data) > 1 else 0.0,
        'stdev': float(np.std(data, ddof=1)) if len(data) > 1 else 0.0,
    }


def print_samples(dist_name, n, samples):
    """Print all samples to console."""
    print(f"\n{dist_name.upper()} - n={n}")
    print("=" * 60)
    print("Samples:")
    for i, val in enumerate(samples):
        if isinstance(val, (np.integer, int)):
            print(f"{val}", end="  " if (i + 1) % 10 != 0 else "\n")
        else:
            print(f"{val:.6f}", end="  " if (i + 1) % 10 != 0 else "\n")
    if n % 10 != 0:
        print()  # newline if not already printed


def print_statistics(dist_name, n, stats):
    """Print descriptive statistics to console."""
    print(f"\nStatistics for {dist_name.upper()} (n={n}):")
    print("-" * 60)
    print(f"  Count:     {stats['count']}")
    print(f"  Min:       {stats['min']:.6f}")
    print(f"  Max:       {stats['max']:.6f}")
    print(f"  Mean:      {stats['mean']:.6f}")
    print(f"  Variance:  {stats['variance']:.6f}")
    print(f"  Std Dev:   {stats['stdev']:.6f}")


def save_data(dist_name, n, samples):
    """Save raw samples to file for histogram generation."""
    filename = os.path.join(OUTPUT_DIR, f"{dist_name}-{n}.txt")
    np.savetxt(filename, samples, fmt='%.6f' if isinstance(samples[0], (float, np.floating)) else '%d')
    return filename


def main():
    """Generate all random variables and save data."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    np.random.seed(SEED)
    
    print("=" * 60)
    print("Random Variable Generation Lab - Group 10")
    print("=" * 60)
    print(f"Seed: {SEED}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    distributions = [
        ('uniform-int', generate_uniform_int, 'Uniform (int)'),
        ('uniform-double', generate_uniform_double, 'Uniform (double)'),
        ('normal', generate_normal, 'Normal'),
        ('exponential', generate_exponential, 'Exponential'),
        ('lognormal', generate_lognormal, 'Lognormal'),
    ]
    
    for dist_key, gen_func, dist_name in distributions:
        for n in SAMPLE_SIZES:
            samples = gen_func(n)
            print_samples(dist_name, n, samples)
            stats = compute_statistics(samples)
            print_statistics(dist_name, n, stats)
            filepath = save_data(dist_key, n, samples)
            print(f"  Data saved to: {filepath}")
            print()
    
    print("=" * 60)
    print("All samples generated successfully!")
    print("Data files saved to:", OUTPUT_DIR)
    print("=" * 60)


if __name__ == '__main__':
    main()
