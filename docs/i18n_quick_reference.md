# i18n Translation Quick Reference

## ✅ Completed (2026-02-13)

**33 new translations added** to both `.pot` and `.po` files with **100% French coverage**.

---

## 📊 Key Numbers

- **Before:** 48 strings
- **After:** 80 strings (.pot) / 83 strings (.po)
- **Added:** +33 translations
- **Coverage:** 100%

---

## 🚀 To Apply (Choose One)

### Option 1: Restart Odoo Server
```bash
sudo systemctl restart odoo
```

### Option 2: Reload Module
```bash
./odoo-bin -c odoo.conf -d your_db -u ngsign_einvoice_odoo --stop-after-init
```

### Option 3: Odoo UI
**Settings** → **Translations** → **Load a Translation** → Select **French**

---

## 📄 Updated Files

| File | Lines | Size | Status |
|------|-------|------|--------|
| `i18n/ngsign_einvoice_odoo.pot` | 484 | 15 KB | ✅ Updated |
| `i18n/fr.po` | 501 | 18 KB | ✅ Updated |

---

## 🧪 Quick Test

After restarting Odoo, verify:

1. **Settings** → Check "MODE TTN" label (should be in French)
2. **Invoice** → Try invalid partner data → Error should be in French
3. **Invoice** → Check "Ouvrir la page de signature" button

---

## 📚 Full Documentation

- **Complete Report:** `docs/i18n_update_complete.md`
- **Missing Report:** `docs/i18n_missing_translations.md`
- **Update Script:** `../update_i18n.sh`

---

## 🎯 Translation Categories Added

✅ **11** Partner validation errors  
✅ **6** API & transaction messages  
✅ **8** Configuration field labels  
✅ **5** Selection options  
✅ **3** UI elements  

**Total: 33 translations**

---

## 💡 Pro Tip

For future updates, use the automated script:
```bash
cd /path/to/odoo
bash /Users/dali/Documents/Dev/odoo/ngsign_einvoice_odoo/update_i18n.sh your_db_name
```
