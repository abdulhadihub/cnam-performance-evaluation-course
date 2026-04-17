import numpy as np
import matplotlib.pyplot as plt
import os

PLOTS_DIR = os.path.dirname(os.path.abspath(__file__))
if PLOTS_DIR.endswith('/code'):
    PLOTS_DIR = os.path.join(os.path.dirname(PLOTS_DIR), 'plots')

DISTRIBUTIONS = [
    ('uniform-int', 'Uniform (Integer)', 'blue'),
    ('uniform-double', 'Uniform (Double)', 'green'),
    ('normal', 'Normal (μ=15, σ=3)', 'red'),
    ('exponential', 'Exponential (λ=0.05)', 'orange'),
    ('lognormal', 'Lognormal (μ_log=2.0, σ_log=1.0)', 'purple'),
]

SAMPLE_SIZES = [10, 100, 1000, 10000]


def load_data(dist_name, n):
    """Load sample data from file."""
    filename = os.path.join(PLOTS_DIR, f"{dist_name}-{n}.txt")
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Data file not found: {filename}")
    return np.loadtxt(filename)


def create_histogram(dist_name, display_name, n, data, color):
    """Create and save a histogram."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    counts, edges, patches = ax.hist(data, bins='sturges', color=color, alpha=0.7, edgecolor='black')
    
    ax.set_xlabel('Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title(f'{display_name}\nn = {n}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    mean = np.mean(data)
    std = np.std(data, ddof=1) if len(data) > 1 else 0
    stats_text = f'n = {len(data)}\nμ = {mean:.4f}\nσ = {std:.4f}'
    ax.text(0.98, 0.97, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    output_file = os.path.join(PLOTS_DIR, f"{dist_name}-{n}.png")
    plt.savefig(output_file, dpi=100, bbox_inches='tight')
    plt.close()
    
    return output_file


def main():
    """Generate all histograms."""
    print("=" * 70)
    print("Histogram Generation")
    print("=" * 70)
    print(f"Plots directory: {PLOTS_DIR}\n")
    
    total = len(DISTRIBUTIONS) * len(SAMPLE_SIZES)
    count = 0
    
    for dist_name, display_name, color in DISTRIBUTIONS:
        for n in SAMPLE_SIZES:
            count += 1
            print(f"[{count}/{total}] Generating histogram: {dist_name} (n={n})...", end=" ")
            
            try:
                data = load_data(dist_name, n)
                output_file = create_histogram(dist_name, display_name, n, data, color)
                print(f"✓ Saved to {os.path.basename(output_file)}")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    print("\n" + "=" * 70)
    print(f"All {total} histograms generated successfully!")
    print("=" * 70)


if __name__ == '__main__':
    main()
