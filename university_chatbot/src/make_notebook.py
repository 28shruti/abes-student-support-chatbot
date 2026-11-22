import nbformat as nbf, pathlib
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s)); code = lambda s: C.append(nbf.v4.new_code_cell(s))
md("# EDA – AI-Powered Chatbot for University Student Support (Project 30)\n**HCLTech Career Shaper Programme · III Year Industry Project · 2025-26**\n\nThis notebook explores `dataset.csv` (500 chatbot sessions), validates data quality, creates the cleaned/pre-processed dataset and records insights that drive the chatbot's escalation design.")
code("""import pandas as pd, numpy as np, matplotlib.pyplot as plt, seaborn as sns, pathlib
from scipy import stats
sns.set_theme(style='whitegrid', context='notebook'); plt.rcParams['figure.dpi']=110
ROOT = pathlib.Path('..'); FIG = ROOT/'figures'; FIG.mkdir(exist_ok=True)
df = pd.read_csv(ROOT/'data'/'dataset_raw.csv'); dd = pd.read_csv(ROOT/'data'/'data_dictionary_original.csv')
print(df.shape); df.head()""")
md("## 1. Data quality checks")
code("""checks = {'rows':len(df),'columns':df.shape[1],'missing values':int(df.isna().sum().sum()),'duplicate rows':int(df.duplicated().sum()),
 'duplicate session_id':int(df.session_id.duplicated().sum()),
 'confidence outside [0,1]':int((~df.confidence_score.between(0,1)).sum()),'escalated not in {0,1}':int((~df.escalated.isin([0,1])).sum()),
 'rating not in 1..5':int((~df.user_rating.between(1,5)).sum())}
display(pd.Series(checks, name='value').to_frame())
display(df.describe(include='all').T)""")
md("**Finding:** the file is already clean – no nulls, duplicates or out-of-range values. Pre-processing therefore focuses on type conversion, validation and *feature engineering*.")
md("## 2. Pre-processing & feature engineering")
code("""clean = df.copy()
clean['session_id'] = clean.session_id.str.strip().str.upper()
for c in ['user_query_type','intent']: clean[c] = clean[c].str.strip().str.lower().astype('category')
clean['escalated'] = clean.escalated.astype('int8'); clean['user_rating'] = clean.user_rating.astype('int8')
clean['confidence_band'] = pd.cut(clean.confidence_score, [0,0.7,0.8,0.9,1.0], labels=['low (<0.70)','medium (0.70-0.79)','high (0.80-0.89)','very high (>=0.90)'], right=False)
clean['low_confidence'] = (clean.confidence_score < 0.70).astype('int8')
clean['satisfied'] = (clean.user_rating >= 4).astype('int8')
clean['dissatisfied'] = (clean.user_rating <= 2).astype('int8')
clean['query_type_num'] = clean.user_query_type.str.extract(r'(\\d)').astype('int8')
clean.to_csv(ROOT/'data'/'dataset.csv', index=False)
print('saved', clean.shape); clean.head()""")
md("## 3. Visualisations")
md("### 3.1 Query volume by intent")
code("""order = clean.intent.value_counts().index
fig, ax = plt.subplots(figsize=(7,4)); sns.countplot(data=clean, y='intent', order=order, color='#4C78A8', ax=ax)
for p in ax.patches: ax.annotate(int(p.get_width()), (p.get_width()+1, p.get_y()+p.get_height()/2), va='center')
ax.set_title('Sessions per intent'); ax.set_xlabel('Number of sessions'); plt.tight_layout(); plt.savefig(FIG/'fig_eda_intent_volume.png', dpi=160); plt.show()""")
md("Traffic is spread fairly evenly: admissions and schedule are the most frequent topics (78 each) and library the least (60) – no single intent dominates, so the classifier must be good across all topics.")
md("### 3.2 Distribution of intent-classification confidence")
code("""fig, ax = plt.subplots(figsize=(7,4)); sns.histplot(clean.confidence_score, bins=25, kde=True, color='#F58518', ax=ax)
ax.axvline(clean.confidence_score.mean(), ls='--', c='k', label=f'mean = {clean.confidence_score.mean():.3f}'); ax.axvline(0.7, ls=':', c='r', label='0.70 low-confidence cut')
ax.set_title('Distribution of confidence_score'); ax.legend(); plt.tight_layout(); plt.savefig(FIG/'fig_eda_confidence_hist.png', dpi=160); plt.show()
print('share below 0.70:', round(clean.low_confidence.mean(),3), '| skew:', round(stats.skew(clean.confidence_score),3))""")
md("Confidence is spread almost uniformly between 0.60 and 1.00 (mean 0.797). About 27 % of sessions (26.8 %) are below 0.70 – these are the turns where a safety-net (rephrase / human hand-over) matters.")
md("### 3.3 Escalation rate by intent")
code("""g = clean.groupby('intent', observed=True).escalated.agg(['mean','sum','count']).sort_values('mean', ascending=False)
fig, ax = plt.subplots(figsize=(7,4)); ax.barh(g.index, g['mean']*100, color='#E45756'); ax.invert_yaxis()
ax.axvline(clean.escalated.mean()*100, ls='--', c='k', label=f'overall {clean.escalated.mean()*100:.1f}%')
for i,(m,s) in enumerate(zip(g['mean'], g['sum'])): ax.text(m*100+0.2, i, f'{m*100:.1f}% ({s})', va='center')
ax.set_xlabel('% of sessions escalated to a human'); ax.set_title('Escalation rate by intent'); ax.legend(); plt.tight_layout(); plt.savefig(FIG/'fig_eda_escalation_by_intent.png', dpi=160); plt.show()
ct = pd.crosstab(clean.intent, clean.escalated); chi2,p,_,_ = stats.chi2_contingency(ct); print(f'chi-square intent vs escalated: chi2={chi2:.2f}, p={p:.3f}')""")
md("Overall only **7.8 %** (39/500) of sessions were escalated. Fees and library show the highest rates (≈10 %) and exams the lowest (4 %), but the chi-square test is **not significant** – differences between intents are within random variation.")
md("### 3.4 Satisfaction ratings")
code("""fig, axs = plt.subplots(1,2, figsize=(11,4))
sns.countplot(data=clean, x='user_rating', color='#54A24B', ax=axs[0]); axs[0].set_title('Rating distribution (1-5)')
sns.barplot(data=clean, x='escalated', y='user_rating', color='#72B7B2', errorbar=('ci',95), ax=axs[1]); axs[1].set_xticklabels(['Handled by bot (0)','Escalated (1)']); axs[1].set_title('Mean rating: bot vs escalated (95% CI)'); axs[1].set_xlabel('')
plt.tight_layout(); plt.savefig(FIG/'fig_eda_ratings.png', dpi=160); plt.show()
a = clean[clean.escalated==0].user_rating; b = clean[clean.escalated==1].user_rating
print('mean rating bot / escalated:', round(a.mean(),2), round(b.mean(),2)); print(stats.mannwhitneyu(a,b))
print('CSAT (rating>=4):', round(clean.satisfied.mean()*100,1),'%   Dissatisfied (<=2):', round(clean.dissatisfied.mean()*100,1),'%')""")
md("Ratings are almost flat (≈18–23 % per star; mean 3.08, CSAT ≈ 41.6 %). Escalated sessions are rated slightly **higher** (3.46 vs 3.05) – consistent with the idea that reaching a human does not hurt satisfaction – but with only 39 escalations the difference is **not statistically significant** (Mann-Whitney p = 0.09).")
md("### 3.5 Confidence vs. escalation and rating")
code("""fig, axs = plt.subplots(1,2, figsize=(11,4))
r = clean.groupby('confidence_band', observed=True)[['escalated','dissatisfied']].mean()*100
r.plot(kind='bar', ax=axs[0], color=['#E45756','#B279A2'], rot=20); axs[0].set_ylabel('% of sessions'); axs[0].set_title('Escalation & dissatisfaction by confidence band'); axs[0].legend(['Escalated','Dissatisfied (<=2)'])
sns.boxplot(data=clean, x='confidence_band', y='user_rating', color='#9ecae9', ax=axs[1]); axs[1].set_title('Rating by confidence band'); axs[1].tick_params(axis='x', rotation=20)
plt.tight_layout(); plt.savefig(FIG/'fig_eda_confidence_vs_outcome.png', dpi=160); plt.show()
print(r.round(1))
rho1 = stats.spearmanr(clean.confidence_score, clean.escalated); rho2 = stats.spearmanr(clean.confidence_score, clean.user_rating)
print('Spearman conf~escalated', rho1); print('Spearman conf~rating', rho2)""")
md("**Key insight:** confidence is essentially *uncorrelated* with both escalation (ρ ≈ 0.04) and rating (ρ ≈ 0.03). In this log, low-confidence answers were **not** escalated more often (6.0 % in the lowest band vs 9.2 % in the highest) – so a pure confidence-threshold policy would not reproduce the historical behaviour. This motivated a **multi-signal escalation policy** (explicit request, sentiment, safety keywords, repeated confusion) instead of confidence alone.")
md("### 3.6 Correlation heat-map and query-type view")
code("""fig, axs = plt.subplots(1,2, figsize=(11,4))
sns.heatmap(clean[['confidence_score','escalated','user_rating','query_type_num','low_confidence','satisfied']].corr(method='spearman'), annot=True, fmt='.2f', cmap='coolwarm', center=0, ax=axs[0]); axs[0].set_title('Spearman correlation matrix')
q = clean.groupby('user_query_type', observed=True).agg(sessions=('session_id','count'), esc=('escalated','mean'), rating=('user_rating','mean'))
axs[1].bar(q.index.str.replace('query_type_','QT'), q.sessions, color='#4C78A8'); axs[1].set_title('Sessions by query type'); axs[1].set_ylabel('sessions')
for i,(s,e) in enumerate(zip(q.sessions,q.esc)): axs[1].text(i, s+1, f'esc {e*100:.0f}%', ha='center', fontsize=9)
plt.tight_layout(); plt.savefig(FIG/'fig_eda_correlation.png', dpi=160); plt.show(); q.round(3)""")
md("## 4. Summary of findings & implications for the chatbot\n"
 "| # | Finding | Implication |\n|---|---|---|\n"
 "| 1 | Data is complete & valid (500 rows, 0 nulls/duplicates) | Only feature engineering needed |\n"
 "| 2 | 7 intents, fairly balanced (60–78 sessions each) | Train a 7-class classifier; no re-sampling needed |\n"
 "| 3 | Mean confidence 0.797; ~27 % below 0.70 | Use a confidence floor and ask the student to rephrase |\n"
 "| 4 | Escalation rate 7.8 %; no significant difference between intents | Escalation must be driven by *content signals*, not topic |\n"
 "| 5 | Confidence ≈ uncorrelated with escalation/rating | Add sentiment, explicit-request and safety rules to the policy |\n"
 "| 6 | CSAT (rating ≥ 4) ≈ 41.6 %; ratings nearly uniform | Target: improve CSAT via better answers + visible human hand-over |\n\n"
 "**Caveat:** the weak relationships between all variables suggest `dataset.csv` is synthetic (generated from the programme's dataset-generation prompt). Conclusions about real-world behaviour should therefore be treated as illustrative; the dataset has no raw text, so a separate labelled utterance corpus and FAQ base were created to train the NLP components (see report §4.3).")
md("## 5. Export updated data dictionary")
code("""new = pd.DataFrame([
 ['confidence_band','categorical string','medium (0.70-0.79)','very high (>=0.90)','low (<0.70)','No','Engineered: confidence_score binned into 4 bands.'],
 ['low_confidence','int8 (binary)','0','1','0','No','Engineered: 1 if confidence_score < 0.70 (bot unsure), else 0.'],
 ['satisfied','int8 (binary)','1','0','1','No','Engineered: 1 if user_rating >= 4 (CSAT numerator).'],
 ['dissatisfied','int8 (binary)','0','1','0','No','Engineered: 1 if user_rating <= 2.'],
 ['query_type_num','int8','5','4','3','No','Engineered: numeric tier (1-5) extracted from user_query_type.']], columns=dd.columns)
full = pd.concat([dd, new], ignore_index=True); full.to_csv(ROOT/'data'/'data_dictionary.csv', index=False)
print(full.shape); full[['column_name','data_type','description']]""")
nb.cells = C; nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
nbf.write(nb, "notebooks/EDA_Notebook.ipynb"); print("notebook written")
