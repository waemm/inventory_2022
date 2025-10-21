#!/bin/bash
# Training Commands Log for Modern Environment Testing
# Generated automatically to track all training commands

echo "=== Training Commands Log ===" > training_commands_log.txt
echo "Date: $(date)" >> training_commands_log.txt
echo "" >> training_commands_log.txt

# Environment setup
ACTIVATE_CMD="source biodata_modern_env/bin/activate"
PYTHONPATH_CMD="export PYTHONPATH=\"src:\$PYTHONPATH\""

echo "Environment setup:" >> training_commands_log.txt
echo "$ACTIVATE_CMD && $PYTHONPATH_CMD" >> training_commands_log.txt
echo "" >> training_commands_log.txt

# Classification training command (completed successfully)
CLASSIF_CMD="python src/class_train.py -t data/classif_splits_test/train_paper_classif.csv -v data/classif_splits_test/val_paper_classif.csv -m allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 -ne 2 -batch 16 -o out/classif_test -r"

echo "Classification training (COMPLETED):" >> training_commands_log.txt
echo "$ACTIVATE_CMD && $PYTHONPATH_CMD && $CLASSIF_CMD" >> training_commands_log.txt
echo "" >> training_commands_log.txt

# NER data generation (COMPLETED)
NER_DATA_CMD="python src/ner_data_generator.py -o data/ner_splits_test --splits 0.7 0.15 0.15 -r data/manual_ner_extraction_test.csv"

echo "NER data generation (COMPLETED):" >> training_commands_log.txt
echo "$ACTIVATE_CMD && $PYTHONPATH_CMD && $NER_DATA_CMD" >> training_commands_log.txt
echo "" >> training_commands_log.txt

# NER training command (COMPLETED)
NER_CMD="python src/ner_train.py -c f1 -m allenai/dsp_roberta_base_dapt_biomed_tapt_rct_500 -ne 2 -t data/ner_splits_test/train_ner.pkl -v data/ner_splits_test/val_ner.pkl -o out/ner_test -batch 16 -rate 2e-5 -decay 0 -r"

echo "NER training (COMPLETED):" >> training_commands_log.txt
echo "$ACTIVATE_CMD && $PYTHONPATH_CMD && $NER_CMD" >> training_commands_log.txt
echo "" >> training_commands_log.txt

# Library upgrades needed
echo "Required library upgrades:" >> training_commands_log.txt
echo "pip install datasets==2.19.0  # Fixed datasets compatibility issue" >> training_commands_log.txt
echo "" >> training_commands_log.txt

echo "Commands logged to training_commands_log.txt"