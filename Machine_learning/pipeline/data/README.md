# pipeline/data — بيانات التدريب

**مصدر البيانات الأصلية موجود في مستودع الفريق:** فرع `remas-mushabbab-attacks-generator`، مجلد `Clear_Attack_Simulation/` (من عمل ريماس). الملفات الستة الأصلية أدناه **مطابقة بايتًا ببايت** لما دُرّب عليه النموذج (قورنت بـSHA-256)، فلا حاجة لنسخها هنا. يلتقط `pipeline/common.py` المجلد تلقائيًا إذا وُجد `Clear_Attack_Simulation/` في جذر المستودع، أو عبر المتغير `MUBSIR_DATA`.
أما ملفات `work/` فمشتقة من سكربتاتنا (`01` و`18` و`21` و`25`) وتُعاد توليدها، ولا حاجة لرفعها.

المجلدان `Clear_Attack_Simulation/` و`work/` مستثناة في `.gitignore`: هي بيانات محاكاة مشتقة من CERT r6.2 (63 ميغابايت) وملكيتها وترخيصها يقرّرهما صاحب المشروع. **النموذج (`../../model`) والاختبارات (`../../tests`) لا تحتاجانها.** تحتاجها فقط سكربتات `pipeline/` و`verify_release.py`.

ضع الملفات التالية في مسارها بالضبط (أو وجّه `MUBSIR_DATA` و`MUBSIR_WORK` إلى مواقعها). التحقق من سلامتها: `sha256sum -c SHA256SUMS.txt` من هذا المجلد.

| الملف (نسبةً إلى هذا المجلد) | SHA-256 (أول 16) |
|---|---|
| `Clear_Attack_Simulation/data/final/behavior_features_r62_ml_final.parquet` | `1aaa189471fb4f57` |
| `Clear_Attack_Simulation/data/final/user_day_injected_r62.parquet` | `d0f960c97b7cbe17` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_channel_days.parquet` | `52ae9eb047a7d9b5` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_user_days.parquet` | `4741e719274b81da` |
| `Clear_Attack_Simulation/data/ground_truth/ground_truth_users.parquet` | `f0d4aeaa74762724` |
| `Clear_Attack_Simulation/data/stages_output/validated_scenario_assignments_r62.parquet` | `039c15f15d6a8bad` |
| `work/evidence_features.parquet` | `094886ac17710eb3` |
| `work/final_changed_features.parquet` | `a787f3f1267cffc3` |
| `work/gap_alt_features.parquet` | `689baa59b3611ccd` |
| `work/prepared_995.parquet` | `aa49c759e42f2c17` |

الملفات في `work/` تُنتَج من `01_prepare.py` و`18` و`21` و`25`؛ والباقي هو مدخلات المحاكاة الأصلية للفريق.
