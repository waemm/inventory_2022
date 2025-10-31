"""
Generate Training Curve Visualizations for Phase 4 Multi-Task Learning

This script creates comprehensive visualizations of the training process:
1. Loss curves (overall, classification, NER, auxiliary)
2. F1 score progression (classification and NER)
3. Combined performance metrics
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Load training history
history_path = Path("../../collab_results/experiment_archives/2025-10-31-rq7i4n/multitask_training/training_history.json")
with open(history_path) as f:
    history = json.load(f)

# Create output directory
output_dir = Path(".")
output_dir.mkdir(exist_ok=True)

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
colors = {
    'overall': '#2E86AB',
    'classif': '#A23B72',
    'ner': '#F18F01',
    'aux': '#C73E1D',
    'baseline': '#6A994E'
}

# Figure 1: Training Loss Curves
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
epochs = list(range(1, 31))

# Overall loss
axes[0, 0].plot(epochs, history['train_loss'], color=colors['overall'], linewidth=2, label='Overall Loss')
axes[0, 0].set_title('Overall Training Loss', fontsize=14, fontweight='bold')
axes[0, 0].set_xlabel('Epoch')
axes[0, 0].set_ylabel('Loss')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()

# Classification loss
axes[0, 1].plot(epochs, history['train_classif_loss'], color=colors['classif'], linewidth=2, label='Classification Loss')
axes[0, 1].set_title('Classification Task Loss', fontsize=14, fontweight='bold')
axes[0, 1].set_xlabel('Epoch')
axes[0, 1].set_ylabel('Loss')
axes[0, 1].grid(True, alpha=0.3)
axes[0, 1].legend()

# NER loss
axes[1, 0].plot(epochs, history['train_ner_loss'], color=colors['ner'], linewidth=2, label='NER Loss')
axes[1, 0].set_title('NER Task Loss', fontsize=14, fontweight='bold')
axes[1, 0].set_xlabel('Epoch')
axes[1, 0].set_ylabel('Loss')
axes[1, 0].grid(True, alpha=0.3)
axes[1, 0].legend()

# Auxiliary loss
axes[1, 1].plot(epochs, history['train_aux_loss'], color=colors['aux'], linewidth=2, label='Auxiliary Loss')
axes[1, 1].set_title('Auxiliary Task Loss (Metadata Prediction)', fontsize=14, fontweight='bold')
axes[1, 1].set_xlabel('Epoch')
axes[1, 1].set_ylabel('Loss')
axes[1, 1].grid(True, alpha=0.3)
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(output_dir / 'training_loss_curves.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Validation F1 Scores
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Classification F1
classif_baseline = 0.8980
axes[0].plot(epochs, history['val_classif_f1'], color=colors['classif'], linewidth=2, marker='o', markersize=4, label='Multi-Task Model')
axes[0].axhline(y=classif_baseline, color=colors['baseline'], linestyle='--', linewidth=2, label='V2 Baseline (0.898)')
axes[0].set_title('Classification F1 Score Progression', fontsize=14, fontweight='bold')
axes[0].set_xlabel('Epoch')
axes[0].set_ylabel('F1 Score')
axes[0].set_ylim([0, 1.0])
axes[0].grid(True, alpha=0.3)
axes[0].legend()
axes[0].annotate(f'Peak: {max(history["val_classif_f1"]):.4f}',
                 xy=(history['val_classif_f1'].index(max(history['val_classif_f1']))+1, max(history['val_classif_f1'])),
                 xytext=(10, -20), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

# NER F1
ner_baseline = 0.7490
axes[1].plot(epochs, history['val_ner_f1'], color=colors['ner'], linewidth=2, marker='o', markersize=4, label='Multi-Task Model')
axes[1].axhline(y=ner_baseline, color=colors['baseline'], linestyle='--', linewidth=2, label='V2 Baseline (0.749)')
axes[1].set_title('NER F1 Score Progression', fontsize=14, fontweight='bold')
axes[1].set_xlabel('Epoch')
axes[1].set_ylabel('F1 Score')
axes[1].set_ylim([0, 1.0])
axes[1].grid(True, alpha=0.3)
axes[1].legend()
axes[1].annotate(f'Peak: {max(history["val_ner_f1"]):.4f}\n+23.8% vs baseline',
                 xy=(history['val_ner_f1'].index(max(history['val_ner_f1']))+1, max(history['val_ner_f1'])),
                 xytext=(10, -30), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.5', fc='lightgreen', alpha=0.7),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

plt.tight_layout()
plt.savefig(output_dir / 'validation_f1_curves.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 3: Combined Performance View
fig, ax = plt.subplots(figsize=(14, 8))

# Combined F1 (weighted average)
combined_f1 = [0.3 * c + 0.7 * n for c, n in zip(history['val_classif_f1'], history['val_ner_f1'])]
combined_baseline = 0.3 * classif_baseline + 0.7 * ner_baseline

ax.plot(epochs, history['val_classif_f1'], color=colors['classif'], linewidth=2, marker='s', markersize=5, label='Classification F1', alpha=0.7)
ax.plot(epochs, history['val_ner_f1'], color=colors['ner'], linewidth=2, marker='^', markersize=5, label='NER F1', alpha=0.7)
ax.plot(epochs, combined_f1, color=colors['overall'], linewidth=3, marker='o', markersize=6, label='Combined F1 (0.3×Classif + 0.7×NER)')
ax.axhline(y=combined_baseline, color=colors['baseline'], linestyle='--', linewidth=2, label=f'Combined Baseline ({combined_baseline:.4f})')

ax.set_title('Multi-Task Learning Performance Overview', fontsize=16, fontweight='bold')
ax.set_xlabel('Epoch', fontsize=12)
ax.set_ylabel('F1 Score', fontsize=12)
ax.set_ylim([0, 1.0])
ax.grid(True, alpha=0.3)
ax.legend(fontsize=11, loc='lower right')

# Add text box with summary
textstr = f'Peak Performance:\n' \
          f'Classification: {max(history["val_classif_f1"]):.4f}\n' \
          f'NER: {max(history["val_ner_f1"]):.4f}\n' \
          f'Combined: {max(combined_f1):.4f}\n\n' \
          f'vs V2 Baseline:\n' \
          f'Classif: {(max(history["val_classif_f1"]) - classif_baseline)*100:.2f}%\n' \
          f'NER: {(max(history["val_ner_f1"]) - ner_baseline)*100:.2f}%\n' \
          f'Combined: {(max(combined_f1) - combined_baseline)*100:.2f}%'

props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=10,
        verticalalignment='top', bbox=props, family='monospace')

plt.tight_layout()
plt.savefig(output_dir / 'combined_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# Figure 4: Loss Reduction Analysis
fig, ax = plt.subplots(figsize=(12, 6))

# Calculate reduction percentages
initial_losses = {
    'Overall': history['train_loss'][0],
    'Classification': history['train_classif_loss'][0],
    'NER': history['train_ner_loss'][0],
    'Auxiliary': history['train_aux_loss'][0]
}

final_losses = {
    'Overall': history['train_loss'][-1],
    'Classification': history['train_classif_loss'][-1],
    'NER': history['train_ner_loss'][-1],
    'Auxiliary': history['train_aux_loss'][-1]
}

reduction = [(initial_losses[k] - final_losses[k]) / initial_losses[k] * 100
             for k in initial_losses.keys()]

x_pos = np.arange(len(initial_losses))
bars = ax.bar(x_pos, reduction, color=[colors['overall'], colors['classif'], colors['ner'], colors['aux']], alpha=0.7)

ax.set_ylabel('Loss Reduction (%)', fontsize=12)
ax.set_title('Training Loss Reduction (Epoch 1 → 30)', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(initial_losses.keys())
ax.set_ylim([0, 100])
ax.grid(True, axis='y', alpha=0.3)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars, reduction)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{val:.1f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

plt.tight_layout()
plt.savefig(output_dir / 'loss_reduction.png', dpi=300, bbox_inches='tight')
plt.close()

print("✅ All visualizations generated successfully!")
print(f"   - training_loss_curves.png")
print(f"   - validation_f1_curves.png")
print(f"   - combined_performance.png")
print(f"   - loss_reduction.png")
