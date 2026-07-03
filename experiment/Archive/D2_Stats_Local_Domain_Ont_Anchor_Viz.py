import json
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# --- 1. Dynamic Path Resolution ---
# Locates 'output' relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
INPUT_PATH = os.path.join(PROJECT_ROOT, "output", "D2_Document_Domain.jsonl")
OUTPUT_IMAGE = os.path.join(PROJECT_ROOT, "output", "D2_Ontological_ZScore_Viz.png")

# Use 'Agg' to ensure PowerShell doesn't hang waiting for a GUI window
plt.switch_backend('Agg')

def generate_dynamic_viz():
    print(f"--- D2_Viz: Syncing with D2_V2 Ground Truth ---")
    
    # 2. Dynamic Data Ingestion
    z_scores = []
    if not os.path.exists(INPUT_PATH):
        print(f"ERROR: {INPUT_PATH} not found. Please run D2_V2 first.")
        return

    try:
        with open(INPUT_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    # Direct extraction from the D2_V2 output
                    z_scores.append(record.get("z_score", 0))
        
        print(f"Successfully ingested {len(z_scores)} records from D2_V3.")
    except Exception as e:
        print(f"Critical error reading data: {e}")
        return

    # 3. Statistical Baseline (Reconstructing the BIZBOK Space)
    # x-axis range adapts to your highest Z-score to show the "distance"
    max_z = max(z_scores) if z_scores else 10
    x = np.linspace(-4, max_z + 4, 1000)
    y = norm.pdf(x, 0, 1) # Standard Normal Baseline

    plt.figure(figsize=(12, 6))
    
    # Plot the BIZBOK Centroid (Governed Knowledge)
    plt.plot(x, y, label='BIZBOK Reference Ontology', color='blue', lw=2)
    plt.fill_between(x, y, where=(x < 2.5), color='green', alpha=0.2, label='Governed Zone (Z < 2.5)')
    
    # 4. Plotting the "Knowledge Gap"
    plt.fill_between(x, y, where=(x >= 2.5), color='red', alpha=0.1, label='Orphan Discovery Zone')
    
    # Scatter plot of actual records from the file
    plt.scatter(z_scores, [0.02]*len(z_scores), color='darkred', marker='x', s=100, 
                label='Ingested RAGBench Orphans', zorder=5)

    # 5. Ph.D. Formatting
    plt.axvline(x=2.5, color='black', linestyle='--', alpha=0.6)
    plt.title("Statistical Ontological Anchor: Empirical Knowledge Gap", fontsize=14, fontweight='bold')
    plt.xlabel("Semantic Distance from BIZBOK Centroid (Z-Score)", fontsize=12)
    plt.ylabel("Probability Density", fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.2)

    # 6. Final Save
    try:
        plt.tight_layout()
        plt.savefig(OUTPUT_IMAGE, dpi=300)
        print(f"SUCCESS: Visualization generated at {OUTPUT_IMAGE}")
    except Exception as e:
        print(f"Save failed: {e}")

if __name__ == "__main__":
    generate_dynamic_viz()