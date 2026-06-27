# Issue: OCR Produces Corrupted Cyrillic Text for Russian-Language Witnesses

**Affects:** Gnedich 1829 Iliad RU witness (`gnedich-1829-ru`) and any future Russian-language scanned-PDF source.  
**Discovered:** 2026-06-27, traced from broken display in Meridian at `/ru/fragment/nms://iliad/book-xxii/death-of-hector`.  
**Status:** Unfixed in Sisyphus. All 437 pages of the Gnedich witness are corrupted in the 2026-06-22 export.

---

## Symptom

The `translated` witness layer for Russian Iliad fragments shows garbled text in Meridian's "Перевод" section:

```
bIM Toa0coM BOMMT,
Cae3Ho Moaswuit a06e3Horo chIHa; HO TOT peg BpaTaMu
Moasa crout, 6becnpegetbHO mbiaaa cpasuteea c leangom..
sKaas06Ho crapey K HeEMy M CAOBa MpocrupaeT U pyKU:
«Lextop, nostio6ienHEtit chu Moi! He qu TH cero uerOBeKa
```

The correct Gnedich text for this passage should be Russian Cyrillic. What is stored is a Latin-character transcription produced by an English-mode OCR engine misidentifying Cyrillic glyphs.

---

## Root Cause

**File:** `sisyphus/phases/phase_a.py`, lines ~215 and ~223  
**Function:** `_ocr_pdf` (scanned-PDF extraction path)

Tesseract is invoked without a `lang` parameter:

```python
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
# ...
text = pytesseract.image_to_string(img)
```

When `lang` is omitted, Tesseract defaults to `eng` (English). Against a Russian-language scan it cannot recognise Cyrillic glyphs and instead substitutes the visually nearest Latin character for each one:

| Cyrillic | Substituted as |
|----------|----------------|
| С | C |
| В | B |
| Н | H |
| Т | T |
| Г | r / I |
| М | M |
| … | … |

The corruption is silent — Tesseract does not error; it merely reports low confidence. The ingestion report for the 2026-06-22 run confirms this:

- `ocr_confidence_mean: 0.44` (44% — catastrophically low)
- `flagged_pages:` **all 437 pages** flagged below threshold

The corrupted `text-full.txt` was then segmented by Phase B into per-fragment YAML files, packed into `export-iliad-20260622.tar.gz`, and ingested by Meridian, which stores and displays it faithfully. The corruption is entirely upstream of Meridian.

---

## Fix

### 1. Pass `lang='rus'` to both pytesseract calls in `phase_a.py`

```python
# Before (broken):
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
# ...
text = pytesseract.image_to_string(img)

# After (fixed):
data = pytesseract.image_to_data(img, lang='rus', output_type=pytesseract.Output.DICT)
# ...
text = pytesseract.image_to_string(img, lang='rus')
```

### 2. Ensure the Tesseract Russian language pack is installed

```bash
# Debian / Ubuntu
sudo apt-get install tesseract-ocr-rus

# macOS (Homebrew)
brew install tesseract-lang
# tesseract-lang includes all language packs including rus

# Verify:
tesseract --list-langs | grep rus
```

### 3. Make the OCR language configurable per-source

Rather than hardcoding `lang='rus'`, thread the language setting through the source config so the same code handles any future language without another code change:

In `config/sources/iliad-gnedich.yaml` (or equivalent):
```yaml
ocr:
  lang: rus
```

In `phase_a.py`, read `lang` from the source config and pass it through:
```python
ocr_lang = source_config.get("ocr", {}).get("lang", "eng")
data = pytesseract.image_to_data(img, lang=ocr_lang, output_type=pytesseract.Output.DICT)
text = pytesseract.image_to_string(img, lang=ocr_lang)
```

English sources continue to work unchanged (`"eng"` is the default).

---

## Recovery Steps (after the fix is applied)

1. Re-run the Sisyphus pipeline for the Iliad Gnedich witness:
   ```bash
   python -m sisyphus run --tradition iliad --source gnedich-1829-ru
   ```
2. Verify OCR confidence is acceptable (target `ocr_confidence_mean > 0.85`; all-pages-flagged must not recur).
3. Re-export: `python -m sisyphus export --tradition iliad`
4. Hand the new `export-iliad-*.tar.gz` to Meridian and re-run `make ingest` there.
5. Confirm the "Перевод" section renders correct Cyrillic in Meridian.

---

## Scope of Affected Data

| Export | Witness | Pages | Status |
|--------|---------|-------|--------|
| `export-iliad-20260622.tar.gz` | `gnedich-1829-ru` | 437 | **All corrupted** |

All other witnesses in the 2026-06-22 exports are either born-digital (no OCR) or English-language (Tesseract `eng` default is correct for them) and are unaffected.
