# R03 news-reasoning data-reuse decision

Status: **USER-RATIFIED LOCAL-SAFETY DECISION; NOT LEGAL ADVICE**  
Decision date: 2026-07-19  
User ratification: 2026-07-19  
Phase: R03  
Scope: existing FinGPT Alpaca/Benzinga news evidence on this workstation

## Decision

Do **not** copy the FinGPT raw-news corpus into this repository.

Reuse it read-only and in place from:

`C:\Users\User\Desktop\FinGPT\data\news_raw`

This preserves the already-fetched evidence without creating a second 2.67 GB
copy, changing provenance, or increasing accidental commit/cloud-sync risk. A
git-ignored local source descriptor under `.research_artifacts/r03-news-reasoning/`
may contain paths, counts, and hashes, but no licensed article text.

## Why copying is not cleared

Alpaca's Terms and Conditions define Content to include general news and third-
party content. They permit personal, non-commercial use but restrict copying,
reproduction, transmission, and distribution without prior written consent.
The current customer agreement separately prohibits reproducing, distributing,
selling, or commercially exploiting market data without written consent.
Alpaca support also states that Alpaca API data cannot be redistributed.

The raw pages identify their policy as `alpaca-benzinga-news`, so third-party
publisher rights may apply in addition to Alpaca's terms. The available terms do
not clearly authorize duplicating the complete news corpus into another project
tree or sending article bodies to an external LLM provider. Absence of an
explicit prohibition on a same-machine second directory is not sufficient legal
clearance for a bulk copy.

Official sources checked 2026-07-19:

- [Alpaca Terms and Conditions](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf)
- [Alpaca Customer Agreement](https://files.alpaca.markets/disclosures/library/AcctAppMarginAndCustAgmt.pdf)
- [Alpaca redistribution support answer](https://alpaca.markets/support/redistribute-alpaca-api)

Written Alpaca/publisher permission or qualified legal review can supersede this
local safety decision.

The user explicitly ratified phase ID R03 and read-only, in-place FinGPT news
reuse on 2026-07-19. The ratification preserves every blocked use below.

## Allowed now

- personal, non-commercial, local provider-free research;
- read-only schema, timestamp, completeness, duplicate, and integrity audits;
- local feature derivation where outputs contain no reconstructable article text;
- use of paths/hashes/counts in tracked research records;
- read-only use of the existing event, sentiment, universe, and bar artifacts,
  subject to the same personal/local boundary;
- local inference only after the R03 charter and implementation approvals.

## Blocked

- copying raw pages or article bodies into this repository;
- commit, push, cloud upload, publication, or sharing of article text;
- embedding article excerpts in fixtures, logs, prompts, tests, or review files;
- sending raw article text to Codex, OpenAI, or any other external model/provider;
- commercial use or making the corpus/results available through an application;
- treating derived artifacts as redistribution-cleared merely because they do
  not contain literal article text.

## Verified local inventory

- Raw root: `data/news_raw`
- JSON files including manifests: 10,270
- Bytes: 2,668,932,157
- Complete ticker-year manifests: 1,000 / 1,000
- Universe represented by manifests: 100 tickers
- Years: 2016–2025
- Declared fetched articles: 436,916
- Manifest policy: `alpaca-benzinga-news` on 1,000 / 1,000 manifests
- Portable aggregate contract:
  `sha256(sorted_utf8(relative_path + NUL + decimal_size + NUL + file_sha256 + LF))`
- All 10,270 JSON files:
  `56f1a5567c1aa5ed5b327201d36f1ca5833381fd3b389279298acdd3a6c1e9d3`
- 9,269 raw page files:
  `4723720c1384723f09c26e9f77941f77a76f1c33d2620e466535eec133213bd9`
- 1,000 ticker-year manifests:
  `dbb5c4110cc2a198ed506cfb6f38b7db172805f46dc1237c5b6de58f9b7fb894`

Important correction: `data/raw/documents.parquet` contains 987 metadata rows
and no article-body column. R4 text lives in `data/news_raw/**/page_NNNN.json`.

## Reopen conditions

Reconsider physical copying or external-provider use only with a written record
covering each of:

1. local bulk reproduction/storage;
2. generation and retention of derived features;
3. transmission of raw text to a named external provider and its retention/
   training policy;
4. publication or redistribution of raw and derived artifacts;
5. commercial versus personal/non-commercial scope.
