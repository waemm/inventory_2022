#!/usr/bin/env python3
"""
Purpose: Use trained BERT model for NER (DIAGNOSTIC VERSION)
Authors: Ana-Maria Istrate and Kenneth Schackart

DIAGNOSTIC VERSION - 2025-10-24
This version includes:
1. Detailed diagnostic logging of dtype, device, and probability calculations
2. Float32 conversion fix for softmax to address PyTorch 2.8 compatibility
3. Comparison between default and float32 softmax outputs
"""

import argparse
import os
import re
import string
from itertools import compress
from statistics import mean
from typing import BinaryIO, Dict, List, NamedTuple, TextIO, cast

import pandas as pd
import torch
import transformers
from pandas.testing import assert_frame_equal
from transformers.modeling_outputs import TokenClassifierOutput
from transformers.tokenization_utils import PreTrainedTokenizer
from transformers.tokenization_utils_base import CharSpan

from inventory_utils.constants import ID2NER_TAG
from inventory_utils.custom_classes import CustomHelpFormatter
from inventory_utils.filing import get_ner_model
from inventory_utils.runtime import get_torch_device
from inventory_utils.wrangling import preprocess_data

pd.options.mode.chained_assignment = None


# ---------------------------------------------------------------------------
class Args(NamedTuple):
    """ Command-line arguments """
    checkpoint: BinaryIO
    infile: TextIO
    out_dir: str


# ---------------------------------------------------------------------------
class SeqPrediction(NamedTuple):
    """
    Attributes of predicted sequence labels

    `seq`: Original sequence
    `word_ids`: List of word indices
    `word_locs`: Dictionary giving character spans for each word
    `preds`: Predicted labels
    `probs`: Predicted label probability
    """
    seq: str
    word_ids: List[int]
    word_locs: Dict[int, CharSpan]
    preds: List[str]
    probs: List[float]


# ---------------------------------------------------------------------------
class NamedEntity(NamedTuple):
    """
    Predicted named entity

    `string`: String predicted to be a named entity
    `label`: Predicted label
    `prob`: Probability of predicted label
    """
    string: str
    label: str
    prob: float


# ---------------------------------------------------------------------------
def get_args() -> Args:
    """ Parse command-line arguments """

    parser = argparse.ArgumentParser(
        description='Predict named entities using trained BERT model',
        formatter_class=CustomHelpFormatter)

    parser.add_argument('-c',
                        '--checkpoint',
                        metavar='CHKPT',
                        type=argparse.FileType('rb'),
                        required=True,
                        help='Trained model checkpoint')
    parser.add_argument('-i',
                        '--input-file',
                        metavar='FILE',
                        type=argparse.FileType('rt', encoding='ISO-8859-1'),
                        required=True,
                        help='Input file for prediction')
    parser.add_argument('-o',
                        '--out-dir',
                        metavar='DIR',
                        type=str,
                        default='out/',
                        help='Directory to output predictions')

    args = parser.parse_args()

    return Args(args.checkpoint, args.input_file, args.out_dir)


# ---------------------------------------------------------------------------
def convert_predictions(seq_preds: SeqPrediction) -> List[NamedEntity]:
    """
    Convert raw predictions to meaningful predictions

    Parameters:
    seq_preds: `SeqPrediction` output from model

    Return: List of `NamedEntity`s
    """

    entities: List[NamedEntity] = []
    began_entity = False

    for loc_id, span in seq_preds.word_locs.items():
        mask = [word_id == loc_id for word_id in seq_preds.word_ids]
        labels = set(compress(seq_preds.preds, mask))
        probs = list(compress(seq_preds.probs, mask))
        substring = seq_preds.seq[span.start:span.end + 1]
        if loc_id > 0:
            if seq_preds.word_locs[loc_id - 1].end == span.start:
                substring = seq_preds.seq[span.start + 1:span.end + 1]
        if any(label[0] == 'B' for label in labels):
            began_entity = True
            label = list(
                compress(labels, [label[0] == 'B' for label in labels]))[0]
            entities.append(NamedEntity(substring, label, mean(probs)))
            prob_count = len(probs)
        elif any(label[0] == 'I' for label in labels) and substring != ' ':
            if not began_entity:
                began_entity = True
                label = list(
                    compress(labels, [label[0] == 'I' for label in labels]))[0]
                entities.append(NamedEntity(substring, label, mean(probs)))
                prob_count = len(probs)
            else:
                last_entity = entities[-1]
                prob = (last_entity.prob * prob_count +
                        sum(probs)) / (prob_count + len(probs))
                prob_count += len(probs)
                entities[-1] = NamedEntity(last_entity.string + substring,
                                           last_entity.label, prob)
        else:
            began_entity = False

    out_entities = []

    for entity in entities:
        if len(entity.string.strip()) == 1 or re.findall(
                'http', entity.string) or len(entity.string.strip()) > 100:
            continue

        out_entities.append(
            NamedEntity(entity.string.strip(), entity.label, entity.prob))

    return out_entities


# ---------------------------------------------------------------------------
def test_convert_predictions() -> None:
    """ Test convert_predictions() """

    seq = 'ALCOdb: Gene Coexpression Database for Microalgae.'
    word_ids = [0, 0, 0, 1, 2, 3, 3, 3, 4, 5, 6, 6, 7]
    word_locs = {
        0: CharSpan(0, 6),
        1: CharSpan(6, 7),
        2: CharSpan(8, 12),
        3: CharSpan(13, 25),
        4: CharSpan(26, 34),
        5: CharSpan(35, 38),
        6: CharSpan(39, 49),
        7: CharSpan(49, 50)
    }
    preds = [
        'B-COM', 'I-COM', 'I-COM', 'I-COM', 'B-FUL', 'I-FUL', 'I-FUL', 'I-FUL',
        'I-FUL', 'I-FUL', 'I-FUL', 'I-FUL', 'I-FUL'
    ]
    probs = [
        0.9914268, 0.9947973, 0.9970761, 0.9951375, 0.98841196, 0.9884289,
        0.99392915, 0.9951815, 0.9865631, 0.99616784, 0.99818134, 0.9980192,
        0.90898293
    ]

    seq_preds = SeqPrediction(seq, word_ids, word_locs, preds, probs)

    expected = [
        NamedEntity('ALCOdb:', 'B-COM', 0.9944334),
        NamedEntity('Gene Coexpression Database for Microalgae.', 'B-FUL',
                    0.98376288)
    ]

    assert convert_predictions(seq_preds) == expected

    seq = 'Inside outside inside inside (inside).'
    word_ids = [0, 1, 2, 3, 4, 5, 6]
    word_locs = {
        0: CharSpan(0, 6),
        1: CharSpan(7, 14),
        2: CharSpan(15, 21),
        3: CharSpan(22, 28),
        4: CharSpan(29, 30),
        5: CharSpan(30, 36),
        6: CharSpan(36, 37)
    }
    preds = ['I-COM', 'O', 'I-FUL', 'I-FUL', 'B-COM', 'I-COM', 'I-COM']
    probs = [0.996, 0.999, 0.998, 0.978, 0.99, 0.98, 0.97]

    seq_preds = SeqPrediction(seq, word_ids, word_locs, preds, probs)

    expected = [
        NamedEntity('Inside', 'I-COM', 0.996),
        NamedEntity('inside inside', 'I-FUL', 0.988),
        NamedEntity('(inside).', 'B-COM', 0.98)
    ]

    assert convert_predictions(seq_preds) == expected

    # Check that single letter and URL entitites are removed
    seq = 'A (https://hello.py)'
    word_ids = [0, 1]
    word_locs = {0: CharSpan(0, 1), 1: CharSpan(2, 20)}
    preds = ['B-COM', 'B-FUL']
    probs = [0.996, 0.999]

    seq_preds = SeqPrediction(seq, word_ids, word_locs, preds, probs)

    expected = []

    assert convert_predictions(seq_preds) == expected


# ---------------------------------------------------------------------------
def predict_sequence(model, device: torch.device, seq: str,
                     tokenizer: PreTrainedTokenizer) -> List[NamedEntity]:
    """
    Run token prediction on sequence

    Parameters:
    `model`: Trained token classification model
    `device`: Device to use
    `seq`: Input string/sequence
    `tokenizer`: Pretrained tokenizer

    Return: List of `NamedEntity`s
    """

    # Diagnostic counter to limit logging output
    if not hasattr(predict_sequence, 'call_count'):
        predict_sequence.call_count = 0
    predict_sequence.call_count += 1

    # Log first 3 predictions to see patterns
    should_log = predict_sequence.call_count <= 3

    with torch.no_grad():
        tokenized_seq = tokenizer(seq,
                                  return_tensors="pt",
                                  padding=True,
                                  truncation=True,
                                  max_length=512).to(device)

        if should_log:
            print("\n" + "="*70)
            print(f"DIAGNOSTIC INFO - Prediction #{predict_sequence.call_count}")
            print("="*70)
            print(f"PyTorch version: {torch.__version__}")
            print(f"Transformers version: {transformers.__version__}")
            print(f"\n--- Model State ---")
            print(f"Model training mode: {model.training}")
            print(f"Model device: {next(model.parameters()).device}")
            print(f"Model dtype: {next(model.parameters()).dtype}")

            print(f"\n--- Input Tokenization ---")
            print(f"Input text sample (first 100 chars): {seq[:100]}...")
            print(f"Input device: {tokenized_seq['input_ids'].device}")
            print(f"Input dtype: {tokenized_seq['input_ids'].dtype}")
            print(f"Input shape: {tokenized_seq['input_ids'].shape}")
            print(f"Token IDs (first 10): {tokenized_seq['input_ids'][0][:10].tolist()}")

        outputs = cast(TokenClassifierOutput, model(**tokenized_seq))
        logits = outputs.logits

        if should_log:
            print(f"\n--- Model Output (Logits) ---")
            print(f"Logits shape: {logits.shape}")
            print(f"Logits dtype: {logits.dtype}")
            print(f"Logits device: {logits.device}")
            print(f"Logits requires_grad: {logits.requires_grad}")
            print(f"Logits range: [{logits.min().item():.6f}, {logits.max().item():.6f}]")
            print(f"Logits mean: {logits.mean().item():.6f}")
            print(f"Logits std: {logits.std().item():.6f}")

            # Show raw logit values for first token
            print(f"\nFirst token logits (all 3 classes): {logits[0][1].tolist()}")

        preds = logits.argmax(dim=-1).cpu().numpy()[0][1:-1]

        # ORIGINAL METHOD: Default softmax (potentially problematic in PyTorch 2.8)
        all_probs_default = torch.nn.functional.softmax(logits,
                                                        dim=-1).cpu().numpy()[0][1:-1]

        # FIX METHOD: Explicit float32 conversion before softmax
        all_probs_float32 = torch.nn.functional.softmax(logits.float(),
                                                        dim=-1).cpu().numpy()[0][1:-1]

        # ALTERNATIVE: log_softmax + exp (numerically stable)
        log_probs = torch.nn.functional.log_softmax(logits, dim=-1)
        all_probs_logsoftmax = torch.exp(log_probs).cpu().numpy()[0][1:-1]

        if should_log:
            print(f"\n--- Softmax Comparison ---")
            print(f"Logits dtype before softmax: {logits.dtype}")
            print(f"Default softmax output dtype: {all_probs_default.dtype}")
            print(f"Float32 softmax output dtype: {all_probs_float32.dtype}")
            print(f"Log-softmax output dtype: {all_probs_logsoftmax.dtype}")

            # Show first few probability values
            print(f"\nSample probabilities (first 5 tokens with predictions):")
            for i in range(min(5, len(preds))):
                pred_idx = preds[i]
                print(f"  Token {i}: pred={pred_idx} ({ID2NER_TAG.get(pred_idx, 'UNKNOWN')})")
                print(f"    default:    {all_probs_default[i][pred_idx]:.8f}")
                print(f"    float32:    {all_probs_float32[i][pred_idx]:.8f}")
                print(f"    log-softmax: {all_probs_logsoftmax[i][pred_idx]:.8f}")
                print(f"    All 3 class probs (default): {all_probs_default[i]}")

            # Calculate differences
            max_diff_f32 = abs(all_probs_default - all_probs_float32).max()
            mean_diff_f32 = abs(all_probs_default - all_probs_float32).mean()
            max_diff_log = abs(all_probs_default - all_probs_logsoftmax).max()
            mean_diff_log = abs(all_probs_default - all_probs_logsoftmax).mean()

            print(f"\nProbability differences (default vs float32):")
            print(f"  Max difference: {max_diff_f32:.8f}")
            print(f"  Mean difference: {mean_diff_f32:.8f}")

            print(f"\nProbability differences (default vs log-softmax):")
            print(f"  Max difference: {max_diff_log:.8f}")
            print(f"  Mean difference: {mean_diff_log:.8f}")

            print("="*70 + "\n")

        # USE THE FLOAT32 FIX - this should resolve PyTorch 2.8 issues
        all_probs = all_probs_float32

        probs = [prob[pred] for pred, prob in zip(preds, all_probs)]
        labels = [ID2NER_TAG[pred] for pred in preds]
        word_ids = tokenized_seq.word_ids()[1:-1]
        word_locs = {
            id: tokenized_seq.word_to_chars(id)
            for id in set(word_ids)
        }

        seq_preds = SeqPrediction(seq, word_ids, word_locs, labels, probs)

    return convert_predictions(seq_preds)


# ---------------------------------------------------------------------------
def predict(model, tokenizer: PreTrainedTokenizer, inputs: pd.DataFrame,
            device: torch.device) -> pd.DataFrame:
    """
    Perform NER prediction on rows of input dataframe

    Parameters:
    `model`: Trained token classification model
    `tokenizer`: Pretrained tokenizer
    `inputs`: Input dataframe
    `device`: Device to use

    Return: Dataframe containining one row per named entity including id, text,
    mention, lable, and probability columns
    """

    pred_df = pd.DataFrame(
        columns=['ID', 'text', 'publication_date', 'mention', 'label', 'prob'])

    for _, row in inputs.iterrows():
        seq = row['title_abstract']
        predicted_labels = predict_sequence(model, device, seq, tokenizer)
        num_preds = len(predicted_labels)
        mentions = [
            x.string.strip(string.punctuation) for x in predicted_labels
        ]
        labels = [x.label[2:] for x in predicted_labels]
        probs = [x.prob for x in predicted_labels]
        pred_df = pd.concat([
            pred_df,
            pd.DataFrame({
                'ID': [row['id']] * num_preds,
                'text': [seq] * num_preds,
                'publication_date': [row['publication_date']] * num_preds,
                'mention': mentions,
                'label': labels,
                'prob': probs
            })
        ])

    return pred_df


# ---------------------------------------------------------------------------
def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deduplicate predicted entities, keeping only highest probability for each
    predicted named entity. Duplicates will still exist for distinct papers.

    Parameters:
    df: Predicted entities dataframe

    Return: Deduplicated dataframe
    """

    unique_df = pd.DataFrame(columns=[*df.columns, 'count'])
    out_df = pd.DataFrame(columns=df.columns)

    # First, remove exact duplicates of a named entity, assigning
    # the highest probability found for that entity
    for _, mention in df.groupby(['ID', 'mention']):
        mention = mention.sort_values('prob', ascending=False)
        mention['count'] = len(mention)
        unique_df = pd.concat([unique_df, mention.head(1)])

    unique_df['uncased_mention'] = unique_df['mention'].str.lower()
    out_df = pd.DataFrame(columns=unique_df.columns)

    # Remove duplicates that differ only in case
    # Choose which to keep by prioritizing number of occurences then prob
    for _, mention in unique_df.groupby(['ID', 'uncased_mention']):
        mention = mention.sort_values(['count', 'prob'], ascending=False)
        out_df = pd.concat([out_df, mention.head(1)])

    out_df.drop(['count', 'uncased_mention'], axis='columns', inplace=True)
    out_df.reset_index(drop=True, inplace=True)

    return out_df


# ---------------------------------------------------------------------------
def test_deduplicate() -> None:
    """ Test deduplicate() """

    in_df = pd.DataFrame(
        [[
            123, 'SAVI Synthetically Accessible Virtual Inventory', 'SAVI',
            'COM', 0.98
        ],
         [
             123, 'SAVI Synthetically Accessible Virtual Inventory',
             'Synthetically Accessible Virtual Inventory', 'FUL', 0.64
         ], [456, 'PANTHER PANTHER PANTHER', 'PANTHER', 'COM', 0.67],
         [456, 'PANTHER PANTHER PANTHER', 'PANTHER', 'COM', 0.95],
         [456, 'PANTHER PANTHER PANTHER', 'PANTHER', 'COM', 0.55],
         [789, 'MicrobPad MD (MicrobPad)', 'MicrobPad', 'FUL', 0.54],
         [789, 'MicrobPad MD (MicrobPad)', 'MicrobPad', 'COM', 0.96],
         [147, 'Chewie-NS Chewie-NS chewie-NS', 'Chewie-NS', 'COM', 0.88],
         [147, 'Chewie-NS Chewie-NS chewie-NS', 'Chewie-NS', 'COM', 0.72],
         [147, 'Chewie-NS Chewie-NS chewie-NS', 'chewie-NS', 'COM', 0.92]],
        columns=['ID', 'text', 'mention', 'label', 'prob'])

    out_df = pd.DataFrame(
        [[
            123, 'SAVI Synthetically Accessible Virtual Inventory', 'SAVI',
            'COM', 0.98
        ],
         [
             123, 'SAVI Synthetically Accessible Virtual Inventory',
             'Synthetically Accessible Virtual Inventory', 'FUL', 0.64
         ], [147, 'Chewie-NS Chewie-NS chewie-NS', 'Chewie-NS', 'COM', 0.88],
         [456, 'PANTHER PANTHER PANTHER', 'PANTHER', 'COM', 0.95],
         [789, 'MicrobPad MD (MicrobPad)', 'MicrobPad', 'COM', 0.96]],
        columns=['ID', 'text', 'mention', 'label', 'prob'])

    assert_frame_equal(deduplicate(in_df), out_df, check_dtype=False)


# ---------------------------------------------------------------------------
def reformat_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reformat output datframe to wide format

    Parameters:
    `df`: Dataframe output by deduplicate()

    Return:
    Wide-format datframe
    """

    df['prob'] = df['prob'].astype(str)

    # Add two dummy rows so that both COM and FUL are present as labels
    df.loc[len(df)] = ['-1', 'foo bar', 'date hold', 'foo', 'COM', '0']
    df.loc[len(df)] = ['-1', 'foo bar', 'date hold', 'bar', 'FUL', '0']
    df = df[df['mention'] != '']

    # For each article, aggregate multiple occurences
    # of same label into single row
    df2 = df['mention'].groupby(
        [df.ID, df.text, df.publication_date,
         df.label]).apply(list).reset_index()
    df2['prob'] = df['prob'].groupby(
        [df.ID, df.text, df.publication_date,
         df.label]).apply(list).reset_index()['prob']

    # Create combined column of mentions and their probs
    df2['mention_prob'] = list(zip(df2['mention'], df2['prob']))

    # Pivot to wide format, each label gets its own column
    df2 = df2.pivot(index=['ID', 'text', 'publication_date'],
                    columns='label',
                    values='mention_prob')

    # Fill missing values
    for col in [
            c for c in list(df2.columns)
            if c not in ['ID', 'text', 'publication_date']
    ]:
        isna = df2[col].isna()
        df2.loc[isna, col] = pd.Series([[[''], ['']]] * isna.sum(),
                                       dtype='object').values

    # Split mentions and probs to their own columns
    # and drop the unsplit columns
    df2[['common_name', 'common_prob']] = pd.DataFrame(df2['COM'].tolist(),
                                                       index=df2.index)
    df2[['full_name', 'full_prob']] = pd.DataFrame(df2['FUL'].tolist(),
                                                   index=df2.index)
    df2.drop(['COM', 'FUL'], inplace=True, axis='columns')

    # Convert lists of multiple mentions to string with commas between
    for col in [
            c for c in list(df2.columns)
            if c not in ['ID', 'text', 'publication_date']
    ]:
        df2[col] = df2[col].fillna('')
        df2[col] = df2[col].apply(', '.join)

    df2.reset_index(inplace=True)

    # Remove the dummy row
    df2 = df2[df2['ID'] != '-1']

    return df2


# ---------------------------------------------------------------------------
def test_reformat_output() -> None:
    """ Test reformat_output() """

    in_df = pd.DataFrame(
        [[
            123, 'SAVI Synthetically Accessible Virtual Inventory',
            '2011-01-01', 'SAVI', 'COM', 0.98
        ],
         [
             123, 'SAVI Synthetically Accessible Virtual Inventory',
             '2011-01-01', 'Synthetically Accessible Virtual Inventory', 'FUL',
             0.64
         ],
         [
             147, 'Chewie-NS Chewie-NS chewie-NS', '2011-01-02', 'Chewie-NS',
             'COM', 0.88
         ], [
             456, 'PANTHER PANTHER LION', '2011-01-03', 'PANTHER', 'COM', 0.95
         ], [456, 'PANTHER PANTHER LION', '2011-01-03', 'LION', 'COM', 0.92],
         [
             789, 'MicrobPad MD (MicrobPad)', '2011-01-04', 'MicrobPad', 'COM',
             0.96
         ]],
        columns=['ID', 'text', 'publication_date', 'mention', 'label', 'prob'])

    out_df = pd.DataFrame([[
        123, 'SAVI Synthetically Accessible Virtual Inventory', '2011-01-01',
        'SAVI', '0.98', 'Synthetically Accessible Virtual Inventory', '0.64'
    ],
                           [
                               147, 'Chewie-NS Chewie-NS chewie-NS',
                               '2011-01-02', 'Chewie-NS', '0.88', '', ''
                           ],
                           [
                               456, 'PANTHER PANTHER LION', '2011-01-03',
                               'PANTHER, LION', '0.95, 0.92', '', ''
                           ],
                           [
                               789, 'MicrobPad MD (MicrobPad)', '2011-01-04',
                               'MicrobPad', '0.96', '', ''
                           ]],
                          columns=[
                              'ID', 'text', 'publication_date', 'common_name',
                              'common_prob', 'full_name', 'full_prob'
                          ])

    assert_frame_equal(reformat_output(in_df),
                       out_df,
                       check_names=False,
                       check_dtype=False)


# ---------------------------------------------------------------------------
def main() -> None:
    """ Main function """

    args = get_args()

    input_df = preprocess_data(args.infile)

    if not os.path.isdir(args.out_dir):
        os.makedirs(args.out_dir)

    out_file = os.path.join(args.out_dir, 'predictions.csv')
    log_file = os.path.join(args.out_dir, 'diagnostic_log.txt')

    device = get_torch_device()

    model, _, tokenizer = get_ner_model(args.checkpoint, device)

    # DIAGNOSTIC: Setup logging to both console and file
    import sys
    from datetime import datetime

    class TeeLogger:
        """Write to both stdout and a file"""
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, 'w')

        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
            self.log.flush()

        def flush(self):
            self.terminal.flush()
            self.log.flush()

    # Redirect stdout to both console and log file
    sys.stdout = TeeLogger(log_file)

    # DIAGNOSTIC: Print environment and model information
    print("\n" + "="*70)
    print("ENHANCED DIAGNOSTIC MODE - Environment Information")
    print(f"Run timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print(f"PyTorch version: {torch.__version__}")
    print(f"Transformers version: {transformers.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA version: {torch.version.cuda}")
        print(f"Device count: {torch.cuda.device_count()}")
        print(f"Current device: {torch.cuda.current_device()}")
        print(f"Device name: {torch.cuda.get_device_name(0)}")
    print(f"Device used: {device}")

    print(f"\n--- Model Information ---")
    print(f"Checkpoint: {args.checkpoint}")
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Model dtype: {next(model.parameters()).dtype}")
    print(f"Model device: {next(model.parameters()).device}")

    # Calculate parameter checksum for verification
    import hashlib
    param_bytes = b''.join([p.cpu().detach().numpy().tobytes()
                            for p in model.parameters()])
    param_hash = hashlib.md5(param_bytes).hexdigest()[:16]
    print(f"Model parameter checksum (MD5, first 16): {param_hash}")

    print(f"\n--- Tokenizer Information ---")
    print(f"Tokenizer class: {type(tokenizer).__name__}")
    print(f"Vocab size: {len(tokenizer)}")

    print(f"\n--- Dataset Information ---")
    print(f"Input papers: {len(input_df)}")

    print("="*70 + "\n")
    print("Starting predictions (will log first 3 in detail)...\n")

    predictions = reformat_output(
        deduplicate(predict(model, tokenizer, input_df, device)))

    predictions.to_csv(out_file, index=False)

    print(f'\n{"="*70}')
    print("DIAGNOSTIC RUN COMPLETE")
    print(f'{"="*70}')
    print(f'Predictions saved to: {out_file}')
    print(f'Diagnostic log saved to: {log_file}')
    print(f"Total predictions made: {len(predictions)}")
    print(f"Unique papers with predictions: {predictions['ID'].nunique()}")
    print(f'{"="*70}\n')

    # Restore stdout
    sys.stdout.log.close()
    sys.stdout = sys.stdout.terminal


# ---------------------------------------------------------------------------
if __name__ == '__main__':
    main()
