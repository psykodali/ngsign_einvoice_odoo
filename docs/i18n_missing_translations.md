# Missing i18n Translations Report

**Generated:** 2026-02-13  
**Module:** ngsign_einvoice_odoo

## Summary

This report lists all translatable strings that are currently **missing** from the translation files (`.pot` and `.po`).

**Total Missing Strings:** 24+

---

## 1. Python Model Strings (17 missing)

These strings are used in Python code with `_()` but not present in the `.pot` file:

### Validation Error Messages (Partner Data)

1. `• Partner VAT/Tax ID is required`
2. `• Partner VAT/Tax ID exceeds 35 characters (current: %d)`
3. `• Partner Name is required`
4. `• Partner Name exceeds 200 characters (current: %d)`
5. `• Partner Address (description) is required`
6. `• Partner Address (description) exceeds 500 characters (current: %d)`
7. `• Street exceeds 35 characters (current: %d)`
8. `• City Name exceeds 35 characters (current: %d)`
9. `• Postal Code exceeds 17 characters (current: %d)`
10. `• Country Code exceeds 6 characters (current: %d)`
11. `Cannot generate e-invoice for %s.\n\nThe following partner information is missing or invalid:\n\n%s\n\nPlease update the partner information and try again.`

### API Error Messages

12. `NGSign API Error: %s`
13. `Unexpected response from NGSign API: %s`
14. `Unexpected response from NGSign API (Global Check): %s - Type: %s`

### Transaction Messages

15. `You can only delete transactions signed in TEST mode.`
16. `No PDS URL found. Please sign the invoice first.`
17. `Invoice signed but failed to download files: %s`

**Location:** `/models/account_move.py`

---

## 2. View/XML Strings (7+ missing)

These strings appear in XML views but are not properly marked for translation:

### Account Move View (`account_move_views.xml`)

1. **Button text:** `Open Signing Page`
2. **Help text:** `Open the Page de Signature to complete signing with your DigiGO or SSCD certificate`

### Configuration Settings (`res_config_settings_views.xml`)

3. **Label:** `TTN MODE`
4. **Label:** `Certificate Type`
5. **Button text:** `BETA: Builtin (Seal V2) PDF generation Layout`
6. **Button text:** `NGSIGN PDF generation Layout`
7. **Button text:** `Developer Options`

### Partner View (`res_partner_views.xml`)

8. **Page/Tab title:** `NGSign` (line 9)

**Locations:** 
- `/views/account_move_views.xml`
- `/views/res_config_settings_views.xml`
- `/views/res_partner_views.xml`

---

## 3. Model Field Labels (Potential Missing)

These field labels should be checked:

### res.config.settings fields

1. `Use V2 Seal Endpoint` (ngsign_use_v2_endpoint)
2. `PDS Base URL` (ngsign_pds_base_url)
3. `Signer Email` (ngsign_signer_email)

**Location:** `/models/res_config_settings.py`

---

## 4. Selection Options

### Certificate Type Options (res_config_settings.py)

These selection labels should be translatable:

1. `SEAL (Automatic Signing)`
2. `DigiGO (User Signature)`
3. `SSCD (USB Token)`

### TTN Mode Options

1. `TEST`
2. `PROD`

**Location:** `/models/res_config_settings.py` (lines 14-30)

---

## How to Fix

### Option 1: Regenerate .pot file using Odoo

```bash
# From Odoo installation directory
./odoo-bin -c odoo.conf -d your_database --i18n-export=ngsign_einvoice_odoo.pot --modules=ngsign_einvoice_odoo --stop-after-init
```

### Option 2: Manual update

1. Update the `.pot` file with missing strings
2. Update the French `.po` file with translations
3. Update/compile translations:

```bash
# Update existing .po file from .pot
msgmerge --update i18n/fr.po i18n/ngsign_einvoice_odoo.pot

# Compile .po to .mo
msgfmt i18n/fr.po -o i18n/fr.mo
```

### Option 3: Use Odoo's built-in update

1. Go to Settings → Translations → Load a Translation
2. Or Settings → Technical → Translations → Export/Import

---

## Translation Status by File

| File | Total Strings | Missing | Status |
|------|--------------|---------|--------|
| account_move.py | 30+ | 17 | ⚠️ 57% missing |
| account_move_views.xml | 10+ | 2 | ⚠️ 20% missing |
| res_config_settings.py | 8+ | 3 | ⚠️ 38% missing |
| res_config_settings_views.xml | 7+ | 5 | ⚠️ 71% missing |
| res_partner_views.xml | 2 | 1 | ⚠️ 50% missing |
| ngsign_client.py | 2 | 0 | ✅ Complete |

---

## Next Steps

1. ✅ **Verified** - Missing strings identified
2. ⏳ **Pending** - Update .pot file
3. ⏳ **Pending** - Update French translations in fr.po
4. ⏳ **Pending** - Test translations in Odoo UI
5. ⏳ **Pending** - Consider adding other language translations

---

## Notes

- Last .pot file update: **2025-12-25 22:00+0000**
- Current date: **2026-02-13**
- Time since last update: **~50 days**
- Recent changes not reflected in translations (e.g., parent contact feature from conversation ca9a338b-e998-4c16-a838-ab930148d1d3)
