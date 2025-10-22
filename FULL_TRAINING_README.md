# Full Training Pipeline with Git Worktree

This setup allows you to run full production training of the biodata inventory ML models while continuing development work uninterrupted.

## Quick Start

### 1. Set up the training environment
```bash
./setup_training_worktree.sh
```
This creates an isolated git worktree at `/Users/warren/development/GBC-training/` where training will run.

### 2. Start full training
```bash
cd /Users/warren/development/GBC-training/
./run_full_single_model_training.sh
```
This will train the `biomed_roberta_rct500` model with full datasets (10 epochs each).

### 3. Monitor progress (from main repo)
```bash
# Quick status check
./monitor_training.sh

# Show recent logs
./monitor_training.sh --logs

# Follow logs in real-time
./monitor_training.sh --follow

# Detailed progress breakdown
./monitor_training.sh --progress
```

## What Gets Trained

**Model**: `biomed_roberta_rct500` (allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500)
- **Classification Model**: Trained on 1,634 manual classifications (10 epochs)
- **NER Model**: Trained on full NER dataset (10 epochs)

## Training Time

**Estimated**: 1-2 hours total
- Classification: ~30-45 minutes
- NER: ~20-30 minutes
- Data preparation and evaluation: ~20 minutes

## Outputs

After training completes, models will be available at:
```
out/classif_train_out/article_classifier.pt     # Classification model
out/ner_train_out/named_entity_recognition.pt   # NER model
```

## Safety Features

- **Backup**: Existing models are automatically backed up before training
- **Logging**: Comprehensive logs with timestamps in `logs/full_training_*.log`
- **Progress Tracking**: Real-time progress monitoring
- **File Protection**: Prevents accidental overwrites
- **Resume Support**: Can restart if interrupted (skips completed steps)

## Monitoring Options

| Command | Description |
|---------|-------------|
| `./monitor_training.sh` | Show current status |
| `./monitor_training.sh --logs` | Show recent log entries |
| `./monitor_training.sh --follow` | Follow logs in real-time |
| `./monitor_training.sh --progress` | Detailed progress breakdown |

## Development Workflow

1. **Start Training**: Run training in the worktree
2. **Continue Development**: Work normally in your main repo
3. **Monitor**: Check progress anytime with monitoring script
4. **Use Models**: Once complete, models are ready for prediction pipeline

## Directory Structure

```
Main Repo: /Users/warren/development/GBC/inventory_2022/
├── setup_training_worktree.sh          # Creates isolated environment
├── monitor_training.sh                 # Monitor from main repo
└── FULL_TRAINING_README.md             # This file

Training Worktree: /Users/warren/development/GBC-training/
├── run_full_single_model_training.sh   # Main training script
├── logs/                               # Training logs
├── model_backups/                      # Backup of existing models
├── out/classif_train_full/             # Training outputs
├── out/ner_train_full/                 # Training outputs
└── out/classif_train_out/              # Final models
    out/ner_train_out/
```

## Troubleshooting

### If training fails:
1. Check the log file: `logs/full_training_*.log`
2. Verify environment: `source biodata_modern_env/bin/activate`
3. Check disk space: `df -h`
4. Restart training (it will skip completed steps)

### If worktree setup fails:
1. Remove existing worktree: `rm -rf /Users/warren/development/GBC-training/`
2. Clean git references: `git worktree prune`
3. Re-run setup script

### Monitor from any location:
```bash
# From anywhere, monitor the training
/Users/warren/development/GBC/inventory_2022/monitor_training.sh --follow
```

## After Training

Once training completes:
1. Models are automatically copied to standard locations
2. Continue using existing prediction scripts
3. Worktree can be removed or kept for future training runs

The trained models will be production-ready and compatible with all existing pipeline scripts.