# pipeline — إعادة إنتاج النموذج النهائي (75 ميزة، LightGBM لكل نافذة)

يُشغَّل من هذا المجلد. المسارات الافتراضية: `data/Clear_Attack_Simulation` (المصدر) و`data/work` (جداول الميزات المشتقة)، ويمكن تغييرها بالمتغيرين `MUBSIR_DATA` و`MUBSIR_WORK`. النموذج المُصدَّر يُكتب في `../model`.

## ترتيب المسار النهائي

| الخطوة | السكربت | الناتج |
|---|---|---|
| 1 | `01_prepare.py` | `data/work/prepared_995.parquet` (995 مستخدمًا، تسميات y_5/y_10/y_20) |
| 2 | `02_split.py` (**قديم**) | `results/user_split.csv`: يُقرأ منه `group` و`stealth` فقط. أعمدة `part` و`rep*` فيه تقسيم عشوائي قديم **لا يستخدمه المسار النهائي** |
| 3 | `14_build_new_rotation_features.py` | `data/work/new_rotation_features.parquet` (مدخل للخطوة التالية؛ مقتطع من 14 القديم) |
| 4 | `18_build_evidence_features.py` | `data/work/evidence_features.parquet`  |
| 5 | `21_build_final_features.py` | `data/work/final_changed_features.parquet` (nr_alt وnr_stealth_acc ونسب p90) |
| 6 | `25_build_gap_alt.py` | `data/work/gap_alt_features.parquet` (nr_gap_alt_G) |
| 7 | `28_final75.py` | `results/final75_*` و`results/models/final75_FINAL75_w{5,10,20}.joblib` |
| 8 | `29_shap75.py` | `results/shap75/` |
| 9 | `31_xgb75.py` (متغير `ALGO`) | `results/xgb75_*` (مقارنة XGBoost للعدل) |
| 10 | `30_export_bundle.py` | يعيد كتابة `../model/` (المعايرة والعتبات المرجعية) |
| 11 | `32_fixed_bands.py` | `results/fixed_bands_*` (العتبات الثابتة 60/85 على الاختبار) |
| 12 | `33_cv_fixed_bands.py` (متغير `ALGO`) | `results/cv75_fixed_bands_*` (CV 5×3) |
| 13 | `34_save_final_split.py` | `results/final_split.csv`: **التقسيم الفعلي** (796 تطوير / 199 اختبار) المعرَّف في الكود (`StratifiedGroupKFold` مجمَّعًا بـ`scenario_id`، أول طية من 5، البذرة 42) |
| 14 | `verify_release.py` | فحوص الإصدار الكاملة (تحتاج `data/`)، راجع `../docs/VERIFICATION.md` |

سكربتات قرارات التصميم (للمرجعية): `22_final_model.py` (خط الأساس بـ74 ميزة)، `24_tune_lightgbm.py` (Optuna، لم تُعتمد)، `26_eval_gap_alt.py` (تقييم nr_gap_alt).

## التحقق
انظر `../docs/VERIFICATION.md` (اختبارات `pytest` في `../tests` لا تحتاج بيانات، و`verify_release.py` يحتاج `data/`).

ملاحظة: `20_build_event_stream.py` و`19_evidence_model.py` (تجارب الأدلة) خارج هذا المستودع لأن المسار النهائي لا يعتمد عليهما.
