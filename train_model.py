"""
ML Model Training Script for Fake Job Detection (FR2)
Trains and compares MULTIPLE models as per project requirement
Dataset: Enhanced Dataset (Kaggle + Pakistani + Modern Jobs)
With Complete Visualization & Metrics
MEMORY OPTIMIZED VERSION

✅ FIXES APPLIED:
   1. class_weight='balanced' — imbalanced dataset fix
      Dataset mein 95% real, 5% fake jobs hain
      Bina balance ke model fake jobs miss karta tha
      Ab fake jobs ko zyada weight milta hai

   2. F1-Score se best model select hota hai
      Accuracy misleading hoti hai imbalanced data mein
      F1 precision + recall dono consider karta hai

   3. probabilities return hoti hain backend ke liye
      Frontend risk_score = probabilities.fake use karega

✅ DATASET UPDATE:
   Old: fake_job_postings.csv (Kaggle 2014 only — 17,880 jobs)
   New: final_dataset.csv (Enhanced — 16,060 jobs)
        - Removed 2000 extra real jobs (better balance)
        - Added 250 new Pakistani FAKE job descriptions
          (WhatsApp scams, send fee, registration fee, etc.)
        - Added 250 new modern REAL job descriptions
          (Pakistani companies, international remote jobs)
        - Result: Better real-world Pakistani job prediction
"""

import pandas as pd
import numpy as np
import pickle
import os
import sys
import gc
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)
import re
import nltk
import ssl
import warnings
import time

# Visualization libraries
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Fix SSL for NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download NLTK data
print("📥 Downloading NLTK data...")
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    print("✅ NLTK data downloaded")
except Exception as e:
    print(f"⚠️ NLTK download issue (continuing anyway): {e}")

# ========================================
# PROJECT INFORMATION
# ========================================
print("\n" + "="*70)
print("🎓 AI-BASED FAKE JOB DETECTION & AWARENESS SYSTEM")
print("   FR2: Text-Based Detection using Multiple ML Models")
print("   University of Education - Final Year Project 2026")
print("="*70)

# ========================================
# 1. Load Dataset
# ✅ UPDATED: Now using final_dataset.csv
#    (Enhanced dataset with Pakistani job descriptions)
# ========================================
print("\n" + "="*70)
print("STEP 1: Loading Enhanced Dataset")
print("✅ Using final_dataset.csv (Kaggle + Pakistani + Modern Jobs)")
print("="*70)

current_dir = Path(__file__).parent
parent_dir  = current_dir.parent

# ✅ UPDATED: final_dataset.csv instead of fake_job_postings.csv
possible_paths = [
    parent_dir / 'database' / 'final_dataset.csv',
    Path('../database/final_dataset.csv'),
    Path('database/final_dataset.csv'),
    Path('Backend/database/final_dataset.csv'),
]

dataset_path = None
for path in possible_paths:
    if path.exists():
        dataset_path = path
        break

if dataset_path is None:
    print("❌ Error: final_dataset.csv not found!")
    print("\n📁 Searched in:")
    for path in possible_paths:
        print(f"   - {path.absolute()}")
    print("\n💡 Please ensure final_dataset.csv exists in Backend/database/")
    print("   This is the enhanced dataset with Pakistani job descriptions.")
    sys.exit(1)

try:
    df = pd.read_csv(dataset_path)
    print(f"✅ Enhanced Dataset loaded successfully!")
    print(f"📂 Path: {dataset_path}")
    print(f"📊 Total records: {len(df):,}")
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    sys.exit(1)

# ========================================
# 2. Data Exploration
# ========================================
print("\n" + "="*70)
print("STEP 2: Data Exploration")
print("="*70)

fake_count = df['fraudulent'].sum()
real_count = len(df) - fake_count

print(f"\n📈 Enhanced Dataset Statistics:")
print(f"├── Total jobs:  {len(df):,}")
print(f"├── Fake jobs:   {fake_count:,} ({fake_count/len(df)*100:.2f}%)")
print(f"└── Real jobs:   {real_count:,} ({real_count/len(df)*100:.2f}%)")
print(f"\n📋 Dataset Improvements:")
print(f"   ✅ Removed 2000 extra real jobs for better balance")
print(f"   ✅ Added 250 Pakistani FAKE job descriptions")
print(f"   ✅ Added 250 modern REAL job descriptions")
print(f"   ✅ WhatsApp scams, send fee patterns included")
print(f"\n⚠️  Dataset IMBALANCED — class_weight='balanced' will fix this")

# ========================================
# 3. Text Preprocessing
# ========================================
print("\n" + "="*70)
print("STEP 3: Text Preprocessing (NLP Pipeline)")
print("="*70)

def clean_text(text):
    """Clean and preprocess text data"""
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = ' '.join(text.split())
    return text

print("🔄 Processing text features...")

df['combined_text'] = (
    df['title'].fillna('') + ' ' +
    df['company_profile'].fillna('') + ' ' +
    df['description'].fillna('') + ' ' +
    df['requirements'].fillna('') + ' ' +
    df['benefits'].fillna('')
)

df['cleaned_text'] = df['combined_text'].apply(clean_text)
df = df[df['cleaned_text'].str.strip() != '']

print(f"✅ Preprocessing complete!")
print(f"📊 Records after cleaning: {len(df):,}")

del df['combined_text']
gc.collect()

# ========================================
# 4. Feature Extraction (TF-IDF)
# ========================================
print("\n" + "="*70)
print("STEP 4: Feature Extraction using TF-IDF (Memory Optimized)")
print("="*70)

gc.collect()

original_size = len(df)
if len(df) > 15000:
    print("\n⚙️ Optimizing for memory efficiency...")
    df = df.sample(n=15000, random_state=42)
    print(f"📊 Using {len(df):,} samples (from {original_size:,}) for training")

tfidf = TfidfVectorizer(
    max_features=1500,
    min_df=10,
    max_df=0.7,
    ngram_range=(1, 1),
    stop_words='english',
    dtype=np.float32
)

print("\n⚙️ Extracting features...")
try:
    X = tfidf.fit_transform(df['cleaned_text'])
    y = df['fraudulent']
    print(f"✅ Feature extraction complete!")
    print(f"📊 Feature matrix shape: {X.shape}")
    print(f"📊 Memory usage: {X.data.nbytes / (1024*1024):.2f} MB")
except MemoryError:
    print("⚠️ Memory error! Reducing features further...")
    tfidf = TfidfVectorizer(
        max_features=800,
        min_df=20,
        max_df=0.6,
        stop_words='english',
        dtype=np.float32
    )
    X = tfidf.fit_transform(df['cleaned_text'])
    y = df['fraudulent']
    print(f"✅ Feature extraction complete (reduced mode)")
    print(f"📊 Feature matrix shape: {X.shape}")

gc.collect()

# ========================================
# 5. Train-Test Split
# ========================================
print("\n" + "="*70)
print("STEP 5: Splitting Dataset (80-20 Split)")
print("="*70)

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"📊 Training set: {X_train.shape[0]:,} samples")
print(f"📊 Testing set:  {X_test.shape[0]:,} samples")

gc.collect()

# ========================================
# 6. Train MULTIPLE Models
# ✅ FIX 1: class_weight='balanced' add kiya
#    Kyun: Dataset mein real 95%, fake 6%
#    Bina balance ke: model real ki taraf bias tha
#    Fake jobs ka risk LOW aa raha tha — GALAT tha
#    Ab: Fake jobs ko zyada weight milta hai training mein
#    Result: Fake jobs ka risk HIGH aayega — SAHI
# ========================================
print("\n" + "="*70)
print("STEP 6: Training MULTIPLE ML Models")
print("✅ FIX: class_weight='balanced' added to all models")
print("="*70)

models = {
    # Naive Bayes: class_weight support nahi karta — as is
    'Naive Bayes': MultinomialNB(),

    # ✅ FIXED: class_weight='balanced' add kiya
    'Logistic Regression': LogisticRegression(
        max_iter=500,
        random_state=42,
        class_weight='balanced'
    ),

    # ✅ FIXED: class_weight='balanced' add kiya
    'Decision Tree': DecisionTreeClassifier(
        random_state=42,
        max_depth=15,
        class_weight='balanced'
    ),

    # ✅ FIXED: class_weight='balanced' add kiya
    'Random Forest': RandomForestClassifier(
        n_estimators=50,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    ),

    # ✅ FIXED: class_weight='balanced' add kiya
    'SVM (Linear)': SVC(
        kernel='linear',
        random_state=42,
        probability=True,
        max_iter=100,
        class_weight='balanced'
    )
}

results         = {}
comparison_data = []

for model_name, model in models.items():
    print(f"\n{'='*70}")
    print(f"🤖 Training: {model_name}")
    print(f"{'='*70}")

    start_time = time.time()
    print("⏳ Training in progress...")

    try:
        model.fit(X_train, y_train)
        training_time = time.time() - start_time

        y_pred = model.predict(X_test)

        accuracy  = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall    = recall_score(y_test, y_pred, zero_division=0)
        f1        = f1_score(y_test, y_pred, zero_division=0)

        results[model_name] = {
            'model':         model,
            'accuracy':      accuracy,
            'precision':     precision,
            'recall':        recall,
            'f1_score':      f1,
            'training_time': training_time,
            'predictions':   y_pred
        }

        comparison_data.append({
            'Model':     model_name,
            'Accuracy':  f"{accuracy*100:.2f}%",
            'Precision': f"{precision*100:.2f}%",
            'Recall':    f"{recall*100:.2f}%",
            'F1-Score':  f"{f1*100:.2f}%",
            'Time':      f"{training_time:.2f}s"
        })

        print(f"✅ {model_name} trained!")
        print(f"📊 Accuracy:  {accuracy*100:.2f}%")
        print(f"📊 Recall:    {recall*100:.2f}%  ← fake detection rate")
        print(f"📊 F1-Score:  {f1*100:.2f}%")
        print(f"⏱️ Time: {training_time:.2f}s")

    except Exception as e:
        print(f"❌ Error training {model_name}: {e}")
        print("   Skipping this model...")
        continue

    gc.collect()

# ========================================
# 7. Model Comparison Table
# ========================================
print("\n" + "="*70)
print("STEP 7: COMPARATIVE ANALYSIS OF ALL MODELS")
print("="*70)

comparison_df = pd.DataFrame(comparison_data)
print("\n" + comparison_df.to_string(index=False))

# ========================================
# 8. Select Best Model
# ✅ FIX 2: Accuracy ki jagah F1-Score se best model select karo
# ========================================
print("\n" + "="*70)
print("STEP 8: Selecting Best Model")
print("✅ FIX: F1-Score use kar rahe hain (accuracy nahi)")
print("="*70)

if not results:
    print("❌ No models were trained successfully!")
    sys.exit(1)

best_model_name = max(results, key=lambda x: results[x]['f1_score'])
best_model      = results[best_model_name]['model']
best_metrics    = results[best_model_name]

print(f"\n🏆 BEST MODEL: {best_model_name}")
print(f"┌{'─'*50}┐")
print(f"│ Accuracy:  {best_metrics['accuracy']*100:>6.2f}%                          │")
print(f"│ Precision: {best_metrics['precision']*100:>6.2f}%                          │")
print(f"│ Recall:    {best_metrics['recall']*100:>6.2f}%  ← fake detection rate      │")
print(f"│ F1-Score:  {best_metrics['f1_score']*100:>6.2f}%  ← selection criteria      │")
print(f"└{'─'*50}┘")

print(f"\n📈 Classification Report:")
print("\n" + classification_report(
    y_test, best_metrics['predictions'],
    target_names=['Real Job', 'Fake Job'],
    zero_division=0
))

# ========================================
# 9. Save Best Model
# ========================================
print("\n" + "="*70)
print("STEP 9: Saving Model Files")
print("="*70)

models_dir = parent_dir / 'models'
models_dir.mkdir(exist_ok=True)

tfidf_path = models_dir / 'tfidf_vectorizer.pkl'
with open(tfidf_path, 'wb') as f:
    pickle.dump(tfidf, f)
print(f"✅ Saved: {tfidf_path}")

model_path = models_dir / 'fake_job_model.pkl'
with open(model_path, 'wb') as f:
    pickle.dump(best_model, f)
print(f"✅ Saved: {model_path} ({best_model_name})")

# ✅ UPDATED: metadata now includes dataset info
metadata = {
    'best_model_name':    best_model_name,
    'accuracy':           best_metrics['accuracy'],
    'precision':          best_metrics['precision'],
    'recall':             best_metrics['recall'],
    'f1_score':           best_metrics['f1_score'],
    'num_features':       X.shape[1],
    'training_samples':   X_train.shape[0],
    'original_dataset_size': original_size,
    'used_dataset_size':  len(df),
    'dataset_name':       'final_dataset.csv',     # ✅ UPDATED
    'dataset_info':       'Kaggle + 250 Pakistani Fake + 250 Modern Real',  # ✅ NEW
    'class_weight':       'balanced',
    'selection_criteria': 'f1_score'
}

metadata_path = models_dir / 'model_metadata.pkl'
with open(metadata_path, 'wb') as f:
    pickle.dump(metadata, f)
print(f"✅ Saved: {metadata_path}")

# ========================================
# 10. Test Samples
# ✅ Now includes Pakistani job test cases
# ========================================
print("\n" + "="*70)
print("STEP 10: Testing Sample Predictions")
print("✅ Including Pakistani job test cases!")
print("="*70)

test_samples = [
    # Original test cases
    ("FAKE", "Urgent! Work from home. Earn $5000/week. Send $200 via WhatsApp! No experience needed. Guaranteed income immediately!"),
    ("REAL", "Software Engineer needed. 3+ years Python experience required. Competitive salary. Apply via company website with CV."),
    ("FAKE", "AMAZING OPPORTUNITY! Pay $500 registration and earn $10,000/month guaranteed! Limited seats. Contact now on WhatsApp!"),
    ("REAL", "Data Analyst position at ABC Corp. Bachelor degree required. 2+ years experience. Health benefits included. Apply online."),
    # ✅ NEW: Pakistani test cases
    ("FAKE", "Earn 50000 rupees daily from home. No experience needed. Just contact us on WhatsApp and send registration fee of 2000 rupees. Guaranteed income every week. Limited seats available apply now urgently."),
    ("REAL", "Habib Bank Limited requires Bank Tellers for Lahore branches. Minimum Bachelor degree required. Fresh graduates welcome. Training provided. Salary as per bank pay scale. Apply through official HBL website."),
    ("FAKE", "Online earning opportunity. Simple copy paste work. Send 1000 rupees fee to get started immediately. Housewives and students can apply. Guaranteed daily payment. WhatsApp now."),
    ("REAL", "Systems Limited hiring Data Analyst with skills in Excel Power BI and SQL. Bachelor degree required. 1-3 years experience preferred. Salary 60000-80000 monthly. Medical and provident fund benefits. Apply through company portal."),
]

print("\n🧪 Testing samples:\n")
for expected, sample in test_samples:
    cleaned    = clean_text(sample)
    features   = tfidf.transform([cleaned])
    prediction = best_model.predict(features)[0]

    try:
        probability = best_model.predict_proba(features)[0]
        fake_prob   = probability[1] * 100
        real_prob   = probability[0] * 100
    except:
        fake_prob = 0.0
        real_prob = 0.0

    result = "FAKE" if prediction == 1 else "REAL"
    status = "✅" if result == expected else "❌"

    print(f"{status} Expected: {expected} | Got: {result}")
    print(f"   Risk Score (fake_prob): {fake_prob:.1f}%")
    print(f"   Text: {sample[:70]}...")
    print()

# ========================================
# 11. CONFUSION MATRIX
# ========================================
print("\n" + "="*70)
print("STEP 11: CONFUSION MATRIX & DETAILED METRICS")
print("="*70)

cm = confusion_matrix(y_test, best_metrics['predictions'])

print("\n📊 Confusion Matrix:")
print(f"\n                Predicted")
print(f"              Real    Fake")
print(f"Actual Real   {cm[0][0]:4d}    {cm[0][1]:4d}")
print(f"       Fake   {cm[1][0]:4d}    {cm[1][1]:4d}")

tn, fp, fn, tp = cm.ravel()

print(f"\n📈 Detailed Metrics:")
print(f"┌{'─'*60}┐")
print(f"│ True Positives (TP):   {tp:>5d}  (Fake correctly identified)   │")
print(f"│ True Negatives (TN):   {tn:>5d}  (Real correctly identified)   │")
print(f"│ False Positives (FP):  {fp:>5d}  (Real marked as fake)         │")
print(f"│ False Negatives (FN):  {fn:>5d}  (Fake missed)                 │")
print(f"└{'─'*60}┘")

specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
fpr         = fp / (fp + tn) if (fp + tn) > 0 else 0
fnr         = fn / (fn + tp) if (fn + tp) > 0 else 0

print(f"\n🎯 Performance Metrics:")
print(f"├── Sensitivity (Recall):  {sensitivity*100:.2f}%  ← fake detection rate")
print(f"├── Specificity:           {specificity*100:.2f}%")
print(f"├── False Positive Rate:   {fpr*100:.2f}%")
print(f"└── False Negative Rate:   {fnr*100:.2f}%  ← lower = better")

try:
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['Real Job', 'Fake Job'],
        yticklabels=['Real Job', 'Fake Job'],
        cbar_kws={'label': 'Count'},
        annot_kws={'size': 16, 'weight': 'bold'}
    )
    plt.title(
        f'Confusion Matrix - {best_model_name}\n'
        f'Accuracy: {best_metrics["accuracy"]*100:.2f}% | F1: {best_metrics["f1_score"]*100:.2f}%',
        fontsize=14, fontweight='bold', pad=20
    )
    plt.ylabel('Actual', fontsize=12, fontweight='bold')
    plt.xlabel('Predicted', fontsize=12, fontweight='bold')
    cm_path = models_dir / 'confusion_matrix.png'
    plt.savefig(cm_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\n✅ Confusion matrix saved: {cm_path}")
    plt.close()
except Exception as e:
    print(f"\n⚠️ Could not save confusion matrix: {e}")

# ========================================
# 12. MODEL COMPARISON CHART
# ========================================
print("\n" + "="*70)
print("STEP 12: MODEL COMPARISON CHART")
print("="*70)

try:
    model_names = list(results.keys())
    accuracies  = [results[m]['accuracy']*100  for m in model_names]
    precisions  = [results[m]['precision']*100 for m in model_names]
    recalls     = [results[m]['recall']*100     for m in model_names]
    f1_scores   = [results[m]['f1_score']*100  for m in model_names]

    fig, ax = plt.subplots(figsize=(14, 7))
    x     = np.arange(len(model_names))
    width = 0.2

    bars1 = ax.bar(x - 1.5*width, accuracies, width, label='Accuracy',  color='#2D3E87', alpha=0.8)
    bars2 = ax.bar(x - 0.5*width, precisions, width, label='Precision', color='#3B82F6', alpha=0.8)
    bars3 = ax.bar(x + 0.5*width, recalls,    width, label='Recall',    color='#F47458', alpha=0.8)
    bars4 = ax.bar(x + 1.5*width, f1_scores,  width, label='F1-Score',  color='#10B981', alpha=0.8)

    ax.set_xlabel('Models', fontsize=13, fontweight='bold')
    ax.set_ylabel('Score (%)', fontsize=13, fontweight='bold')
    ax.set_title(
        'Model Performance Comparison - Fake Job Detection\n'
        '(Enhanced Dataset: Kaggle + Pakistani + Modern Jobs)',
        fontsize=14, fontweight='bold', pad=20
    )
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=20, ha='right', fontsize=11)
    ax.legend(fontsize=11, loc='lower right')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    ax.set_ylim(0, 110)

    for bars in [bars1, bars2, bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{height:.0f}%', ha='center', va='bottom',
                fontsize=8, fontweight='bold'
            )

    plt.tight_layout()
    comparison_path = models_dir / 'model_comparison.png'
    plt.savefig(comparison_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Model comparison saved: {comparison_path}")
    plt.close()
except Exception as e:
    print(f"⚠️ Could not save model comparison: {e}")

# ========================================
# 13. CLASS DISTRIBUTION
# ========================================
print("\n" + "="*70)
print("STEP 13: DATASET CLASS DISTRIBUTION")
print("="*70)

try:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    train_counts = y_train.value_counts()
    colors  = ['#2D3E87', '#F47458']
    explode = (0.05, 0.05)

    ax1.pie(
        [train_counts[0], train_counts[1]],
        labels=['Real Jobs', 'Fake Jobs'],
        autopct='%1.1f%%', colors=colors,
        explode=explode, startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )
    ax1.set_title(
        f'Training Set Distribution\nTotal: {len(y_train):,} samples',
        fontsize=12, fontweight='bold', pad=15
    )

    test_counts = y_test.value_counts()
    ax2.pie(
        [test_counts[0], test_counts[1]],
        labels=['Real Jobs', 'Fake Jobs'],
        autopct='%1.1f%%', colors=colors,
        explode=explode, startangle=90,
        textprops={'fontsize': 11, 'weight': 'bold'}
    )
    ax2.set_title(
        f'Test Set Distribution\nTotal: {len(y_test):,} samples',
        fontsize=12, fontweight='bold', pad=15
    )

    plt.suptitle(
        'Class Distribution in Enhanced Dataset',
        fontsize=14, fontweight='bold', y=1.02
    )
    plt.tight_layout()
    distribution_path = models_dir / 'class_distribution.png'
    plt.savefig(distribution_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Class distribution saved: {distribution_path}")
    plt.close()
except Exception as e:
    print(f"⚠️ Could not save class distribution: {e}")

# ========================================
# 14. TRAINING TIME COMPARISON
# ========================================
print("\n" + "="*70)
print("STEP 14: TRAINING TIME ANALYSIS")
print("="*70)

try:
    training_times = [results[m]['training_time'] for m in model_names]
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(model_names, training_times, color='#F47458', alpha=0.7)
    ax.set_xlabel('Training Time (seconds)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Models', fontsize=12, fontweight='bold')
    ax.set_title('Model Training Time Comparison', fontsize=14, fontweight='bold', pad=15)
    ax.grid(axis='x', alpha=0.3, linestyle='--')

    for bar, time_val in zip(bars, training_times):
        width = bar.get_width()
        ax.text(
            width + 0.1, bar.get_y() + bar.get_height()/2,
            f'{time_val:.2f}s', ha='left', va='center',
            fontsize=10, fontweight='bold'
        )

    plt.tight_layout()
    time_path = models_dir / 'training_time.png'
    plt.savefig(time_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✅ Training time chart saved: {time_path}")
    plt.close()
except Exception as e:
    print(f"⚠️ Could not save training time chart: {e}")

# ========================================
# 15. SAVE COMPLETE RESULTS REPORT
# ========================================
print("\n" + "="*70)
print("STEP 15: SAVING COMPLETE RESULTS REPORT")
print("="*70)

report_path = models_dir / 'training_report.txt'
try:
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("AI-BASED FAKE JOB DETECTION - TRAINING REPORT\n")
        f.write("University of Education - Final Year Project 2026\n")
        f.write("="*70 + "\n\n")

        f.write("FIXES APPLIED IN THIS VERSION:\n")
        f.write("-" * 70 + "\n")
        f.write("1. class_weight='balanced' — imbalanced dataset fix\n")
        f.write("   Dataset: real majority, fake minority\n")
        f.write("   Fix: Fake jobs get higher weight during training\n")
        f.write("   Result: Fake jobs now correctly get HIGH risk scores\n\n")
        f.write("2. F1-Score for best model selection (was accuracy before)\n")
        f.write("   Reason: Accuracy is misleading for imbalanced datasets\n")
        f.write("   F1 considers both precision and recall\n\n")
        f.write("3. Enhanced Dataset (final_dataset.csv)\n")
        f.write("   Old: fake_job_postings.csv — Kaggle 2014 only\n")
        f.write("   New: final_dataset.csv — Kaggle + Pakistani + Modern\n")
        f.write("   Added 250 Pakistani fake job descriptions\n")
        f.write("   Added 250 modern real job descriptions\n")
        f.write("   Removed 2000 extra real jobs for better balance\n\n")

        f.write("DATASET INFORMATION:\n")
        f.write("-" * 70 + "\n")
        f.write(f"Dataset File: final_dataset.csv\n")
        f.write(f"Dataset Info: Kaggle + 250 Pakistani Fake + 250 Modern Real\n")
        f.write(f"Original Dataset Size: {original_size:,}\n")
        f.write(f"Used for Training: {len(df):,}\n")
        f.write(f"Real Jobs: {real_count:,} ({real_count/original_size*100:.2f}%)\n")
        f.write(f"Fake Jobs: {fake_count:,} ({fake_count/original_size*100:.2f}%)\n")
        f.write(f"Training Samples: {X_train.shape[0]:,}\n")
        f.write(f"Testing Samples: {X_test.shape[0]:,}\n")
        f.write(f"Feature Dimensions: {X.shape[1]:,}\n")
        f.write(f"Class Weight: balanced\n")
        f.write(f"Best Model Selection: F1-Score\n\n")

        f.write("="*70 + "\n")
        f.write("MODEL COMPARISON:\n")
        f.write("="*70 + "\n")
        f.write(comparison_df.to_string(index=False))
        f.write("\n\n")

        f.write("="*70 + "\n")
        f.write(f"BEST MODEL: {best_model_name}\n")
        f.write("="*70 + "\n")
        f.write(f"Accuracy:  {best_metrics['accuracy']*100:.2f}%\n")
        f.write(f"Precision: {best_metrics['precision']*100:.2f}%\n")
        f.write(f"Recall:    {best_metrics['recall']*100:.2f}%  (fake detection rate)\n")
        f.write(f"F1-Score:  {best_metrics['f1_score']*100:.2f}%  (selection criteria)\n")
        f.write(f"Training Time: {best_metrics['training_time']:.2f} seconds\n\n")

        f.write("CONFUSION MATRIX:\n")
        f.write("-" * 70 + "\n")
        f.write(f"                Predicted\n")
        f.write(f"              Real    Fake\n")
        f.write(f"Actual Real   {cm[0][0]:4d}    {cm[0][1]:4d}\n")
        f.write(f"       Fake   {cm[1][0]:4d}    {cm[1][1]:4d}\n\n")

        f.write("DETAILED METRICS:\n")
        f.write("-" * 70 + "\n")
        f.write(f"TP: {tp:5d}  Fake jobs correctly identified\n")
        f.write(f"TN: {tn:5d}  Real jobs correctly identified\n")
        f.write(f"FP: {fp:5d}  Real jobs incorrectly flagged\n")
        f.write(f"FN: {fn:5d}  Fake jobs missed\n\n")

        f.write(f"Sensitivity (Recall): {sensitivity*100:.2f}%\n")
        f.write(f"Specificity:          {specificity*100:.2f}%\n")
        f.write(f"False Positive Rate:  {fpr*100:.2f}%\n")
        f.write(f"False Negative Rate:  {fnr*100:.2f}%\n\n")

        f.write("="*70 + "\n")
        f.write("CLASSIFICATION REPORT:\n")
        f.write("="*70 + "\n")
        f.write(classification_report(
            y_test, best_metrics['predictions'],
            target_names=['Real Job', 'Fake Job'],
            zero_division=0
        ))

        f.write("\n" + "="*70 + "\n")
        f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n")

    print(f"✅ Complete report saved: {report_path}")
except Exception as e:
    print(f"⚠️ Could not save report: {e}")

# ========================================
# 16. PRINT FINAL SUMMARY
# ========================================
print("\n" + "="*70)
print("🎉 TRAINING COMPLETE - SUMMARY")
print("="*70)
print(f"\n📊 Dataset:     final_dataset.csv (Enhanced)")
print(f"📊 Best Model:  {best_model_name}")
print(f"📊 Accuracy:    {best_metrics['accuracy']*100:.2f}%")
print(f"📊 Precision:   {best_metrics['precision']*100:.2f}%")
print(f"📊 Recall:      {best_metrics['recall']*100:.2f}%  ← fake detection rate")
print(f"📊 F1-Score:    {best_metrics['f1_score']*100:.2f}%")

print(f"\n✅ Fixes Applied:")
print(f"   1. Enhanced dataset with Pakistani job descriptions ✅")
print(f"   2. class_weight='balanced' — imbalanced dataset fixed ✅")
print(f"   3. F1-Score se best model select kiya ✅")
print(f"   4. Pakistani fake job patterns now in training data ✅")

print(f"\n📁 Files Saved in: {models_dir}")
print(f"   ✅ fake_job_model.pkl")
print(f"   ✅ tfidf_vectorizer.pkl")
print(f"   ✅ model_metadata.pkl")
print(f"   ✅ confusion_matrix.png")
print(f"   ✅ model_comparison.png")
print(f"   ✅ class_distribution.png")
print(f"   ✅ training_time.png")
print(f"   ✅ training_report.txt")

print("\n" + "="*70)
print("🚀 Ab backend restart karo:")
print("   cd Backend && python app.py")
print("="*70)