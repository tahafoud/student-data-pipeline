Taha Foud Alshaweh


# Student Data Pipeline

### Data Engineering — Multi-Source Data Integration Pipeline
تطبيق Python احترافي يقوم ببناء **Data Engineering Pipeline** كامل: يستخرج بيانات الطلاب من ثلاثة مصادر مختلفة (CSV، REST API، SQLite)، يتحقق من جودتها، يدمجها، ينظفها، يحوّلها، ثم ينتج Dataset نهائي جاهز للتحليل و Machine Learning.

---

## 1. Project Overview

المؤسسة التعليمية تمتلك بيانات طلابها موزعة على ثلاثة أنظمة منفصلة:

| # | المصدر | البيانات |
|---|--------|----------|
| 1 | `data/raw/students.csv` | البيانات الأساسية: student_id, student_name, age, major, city |
| 2 | REST API (محلي / Mock) | البيانات الأكاديمية: gpa, attendance, status |
| 3 | `database/students.db` (SQLite) | المقررات والتسجيل: courses, enrollments (score, semester) |

هذا المشروع يبني Pipeline كامل ينفّذ:

```
Extract → Validate → Clean → Integrate → Transform → Final Validation → Load
```

الناتج النهائي: `data/processed/final_dataset.csv` — ملف موحّد، نظيف، خالٍ من السجلات غير الصالحة وجاهز للاستخدام في Data Analysis وBI وML.

## 2. Architecture

```
student_data_pipeline/
│
├── app/
│   ├── sources/            # Extract layer — كل مصدر بملفه الخاص
│   │   ├── csv_source.py
│   │   ├── api_source.py
│   │   └── database_source.py
│   │   └── mock_api_server.py   # خادم REST API محلي يحاكي مصدرًا خارجيًا
│   │
│   ├── transformation/
│   │   ├── cleaner.py       # Data Cleaning (تنظيف كل مصدر على حدة)
│   │   ├── transformer.py   # Data Transformation (أعمدة، أنواع، قيم مفقودة)
│   │   └── integration.py   # Data Integration (الدمج على student_id)
│   │
│   ├── validation/
│   │   └── quality.py       # Data Quality Rules + الفصل بين Valid/Rejected
│   │
│   ├── output/
│   │   └── csv_writer.py    # Load stage
│   │
│   └── utils/
│       ├── logger.py        # إعداد الـ Logging المركزي
│       ├── config_loader.py # قراءة config.yaml
│       ├── metrics.py       # Pipeline Metrics
│       └── exceptions.py    # أخطاء مخصصة للـ Pipeline
│
├── data/
│   ├── raw/students.csv
│   ├── processed/final_dataset.csv
│   └── rejected/rejected_records.csv
│
├── database/
│   ├── students.db
│   └── build_database.py    # ينشئ قاعدة البيانات ببيانات تجريبية
│
├── tests/
│   └── test_pipeline.py     # 8 اختبارات مطلوبة
│
├── logs/pipeline.log
├── config.yaml
├── main.py
├── requirements.txt
└── README.md
```

كل مرحلة من مراحل الـ Pipeline معزولة في وحدتها الخاصة (Single Responsibility)، بحيث يمكن تعديل أو استبدال أي مرحلة دون التأثير على البقية — وهذا ما يجعل البنية قابلة لإعادة الاستخدام والتوسع (انظر قسم "Reusable Architecture" أدناه).

## 3. Data Sources

**1) CSV** — `data/raw/students.csv`: بيانات أساسية عن 20+ طالبًا، تحتوي عمدًا على مشاكل جودة (قيم مكررة، عمر غير منطقي، فراغات زائدة، اختلاف حالة الأحرف، قيمة student_id مفقودة) لاختبار مراحل التنظيف والتحقق.

**2) REST API** — نظرًا لعدم توفر اتصال إنترنت في بيئة التطوير، تم بناء **Mock API محلي** (`app/sources/mock_api_server.py`) يعمل بالضبط كأي REST API حقيقي: يُستدعى عبر HTTP باستخدام مكتبة `requests`، يعيد JSON، ويمكن أن يفشل بنفس طرق فشل أي API حقيقي (Timeout, Connection Error, HTTP Error, Invalid JSON). هذا الخيار مذكور صراحة في التكليف كبديل عند تعذّر الاتصال بالإنترنت. لاستخدام API حقيقي بدلاً منه، يكفي تغيير `use_mock: false` و `base_url` في `config.yaml` دون تعديل أي كود.

**3) SQLite Database** — `database/students.db`: جدولا `courses` و `enrollments` مرتبطان عبر `course_id`، ومرتبطان ببيانات الطلاب عبر `student_id`. يتم إنشاء القاعدة تلقائيًا عند أول تشغيل عبر `database/build_database.py` إن لم تكن موجودة.

## 4. ETL Pipeline

| المرحلة | الوصف | الوحدة المسؤولة |
|---|---|---|
| **Extract** | استخراج البيانات من المصادر الثلاثة مع معالجة كاملة للأخطاء | `app/sources/*` |
| **Validate (Sources)** | فحص تشخيصي أولي لكل مصدر (IDs مفقودة/مكررة، قيم خارج النطاق) — تسجيل فقط بدون حذف | `app/validation/quality.py::validate_sources` |
| **Clean** | إزالة التكرار، توحيد النصوص (حالة الأحرف والمسافات)، تحويل الفراغات إلى NaN | `app/transformation/cleaner.py` |
| **Integrate** | دمج المصادر الثلاثة على `student_id` (CSV كمحور أساسي + LEFT JOIN) | `app/transformation/integration.py` |
| **Transform** | توحيد أسماء الأعمدة، تحويل الأنواع، معالجة القيم المفقودة، إضافة أعمدة مشتقة | `app/transformation/transformer.py` |
| **Final Validation** | تطبيق قواعد الجودة السبع وفصل السجلات الصالحة عن المرفوضة | `app/validation/quality.py::validate_final_data` |
| **Load** | حفظ `final_dataset.csv` و `rejected_records.csv` | `app/output/csv_writer.py` |

تسلسل التنفيذ الكامل موجود في `main.py::run_pipeline()`، وهو مطابق للتصميم المقترح في التكليف.

## 5. Data Quality

**قواعد التحقق النهائية (Rules)**، مطبّقة في `app/validation/quality.py`:

1. `student_id` لا يجوز أن يكون NULL
2. `student_id` يجب أن يكون فريدًا
3. `age` يجب أن يكون بين 16 و 80
4. `GPA` يجب أن يكون بين 0 و 4
5. `attendance` يجب أن يكون بين 0 و 100
6. `avg_score` يجب أن يكون بين 0 و 100
7. `student_id` يجب أن يكون قابلاً للتحويل الرقمي (متوافقًا بين المصادر)

أي سجل يفشل في أحد هذه القواعد يُنقل إلى `data/rejected/rejected_records.csv` مع سبب الرفض (`error_reason`)، ولا يظهر إطلاقًا في `final_dataset.csv`.

**استراتيجية معالجة القيم المفقودة** (موثّقة أيضًا داخل `transformer.py`):
- **GPA المفقود** → يُملأ بـ *median* العمود (أكثر مقاومة للقيم المتطرفة من المتوسط).
- **Attendance المفقود** → يُملأ بقاعدة عمل ثابتة (75)، وهي أول عتبة "Good".
- **Age المفقود** → لا يُخمَّن، بل يُعتبر مخالفة جودة ويُرفض السجل صراحة في مرحلة التحقق النهائية.

## 6. Installation

```bash
pip install -r requirements.txt
```

## 7. Running

```bash
python main.py
```

عند أول تشغيل سيتم إنشاء `database/students.db` تلقائيًا إن لم يكن موجودًا، وسيبدأ خادم الـ Mock API المحلي في خيط خلفي (Background Thread) تلقائيًا.

لتشغيل الاختبارات:

```bash
python -m unittest discover -s tests -v
# أو، إذا كانت pytest مثبتة:
pytest tests/ -v
```

## 8. Output

| الملف | الوصف |
|---|---|
| `data/processed/final_dataset.csv` | Dataset النهائي: موحّد، نظيف، خالٍ من السجلات غير الصالحة |
| `data/rejected/rejected_records.csv` | السجلات المرفوضة مع سبب الرفض (`student_id,error_reason`) |
| `logs/pipeline.log` | سجل تنفيذ كامل لكل مرحلة من مراحل الـ Pipeline |
| Console output | ملخص تنفيذي (Pipeline Execution Summary) بعد كل تشغيل |

---

## Excellence Requirements (متطلبات التميز) المُنفَّذة

1. **Pipeline Configuration** — `config.yaml` يحدد مسارات الملفات وإعدادات كل مصدر (بما فيها التبديل بين Mock API و API حقيقي) دون لمس الكود.
2. **Data Lineage** — عمود `source` في الناتج النهائي يوثّق أي المصادر ساهمت في كل سجل (مثل `CSV+API+DATABASE`).
3. **Pipeline Metrics** — `app/utils/metrics.py` يحسب Total/Valid/Rejected/Duplicate Records ووقت المعالجة، ويُطبع كملخص تنفيذي.
4. **Reusable Architecture** — إضافة مصدر جديد (Excel, JSON, MongoDB...) تتطلب فقط ملفًا جديدًا في `app/sources/` يعيد DataFrame بنفس المفتاح `student_id`، دون إعادة كتابة بقية الـ Pipeline.

*(لم يتم تنفيذ Incremental Processing في هذه النسخة؛ الـ Pipeline يعالج كامل البيانات في كل تشغيل — انظر السؤال 10 أدناه لشرح كيفية تطويره مستقبلاً.)*

---

## الأسئلة النهائية

**1. لماذا نحتاج إلى Data Pipeline عند التعامل مع مصادر متعددة؟**
لأن البيانات القادمة من أنظمة مختلفة تختلف في الشكل والجودة وطريقة الوصول إليها. بدون Pipeline موحّد، سيضطر كل تحليل أو نموذج للتعامل يدويًا مع هذا التشتت، مما يكرر الجهد ويزيد احتمال الأخطاء. الـ Pipeline يوفر مسارًا آليًا وقابلًا لإعادة التشغيل يضمن أن كل من يستخدم البيانات النهائية يحصل على نفس المستوى من الجودة والاتساق.

**2. ما الفرق بين Raw Data و Processed Data؟**
الـ Raw Data هي البيانات كما وصلت من المصدر مباشرة (ملف CSV، استجابة API، جدول قاعدة بيانات) دون أي تعديل — قد تحتوي أخطاء، تكرارًا، أو قيمًا مفقودة. الـ Processed Data هي نتيجة تمرير هذه البيانات عبر مراحل التنظيف والتحويل والتحقق، فتصبح موحّدة الشكل، خالية من المشاكل المعروفة، وجاهزة للاستخدام المباشر في التحليل أو النمذجة.

**3. ما الفرق بين Extract و Transform و Load؟**
- **Extract**: سحب البيانات من مصدرها الأصلي كما هي (CSV, API, DB).
- **Transform**: تعديل شكل البيانات ومحتواها — تنظيف، توحيد أنواع، معالجة قيم مفقودة، إنشاء أعمدة مشتقة — لتصبح متوافقة مع الاستخدام المطلوب.
- **Load**: كتابة البيانات النهائية إلى وجهتها (هنا: ملف CSV) لتصبح متاحة للاستخدام من قبل أنظمة أو محللين آخرين.

**4. ما المشاكل التي واجهتها أثناء دمج البيانات؟**
أبرز مشكلة كانت اختلاف نوع عمود `student_id` بين المصادر (نص في CSV مقابل رقم صحيح في API وSQLite)، مما تسبب في فشل عملية الـ merge حتى تمت معايرة النوع قبل الدمج. مشكلة أخرى كانت أن مصدر SQLite يحتوي على عدة سجلات (مقررات) لكل طالب، بينما CSV وAPI يحتويان سجلًا واحدًا لكل طالب — فاحتجت إلى تجميع (aggregate) بيانات SQLite (متوسط الدرجات، عدد المقررات) قبل دمجها بالمفتاح المشترك.

**5. كيف تعاملت مع Missing Values؟**
باستراتيجية مختلفة لكل عمود حسب طبيعته: `GPA` المفقود يُملأ بالوسيط (median) لأنه أقل تأثرًا بالقيم المتطرفة، `attendance` المفقود يُملأ بقاعدة عمل ثابتة (75)، أما `age` المفقود فلا يُخمَّن إطلاقًا بل يُرفض السجل صراحة لأن تخمين العمر قد يكون مضللًا في تحليل لاحق.

**6. كيف تعاملت مع Duplicate Records؟**
عبر `drop_duplicates` على المفتاح المناسب لكل مصدر (`student_id` في CSV وAPI، وثلاثية `student_id/course/semester` في SQLite)، مع الاحتفاظ بأول ظهور وتسجيل عدد السجلات المحذوفة في الـ log. أي تكرار يتسرب حتى مرحلة التحقق النهائي (Rule 2) يُرفض أيضًا هناك كخط دفاع ثانٍ.

**7. كيف تعاملت مع Invalid Records؟**
عبر مرحلة تحقق نهائية (`validate_final_data`) تطبّق قواعد الجودة السبع على كل سجل بعد الدمج والتحويل، وتفصل النتيجة إلى DataFrame صالح وآخر مرفوض مع توثيق سبب الرفض لكل سجل، ثم يُحفظ المرفوض في `rejected_records.csv` بدلاً من حذفه بصمت — لضمان إمكانية مراجعته لاحقًا.

**8. لماذا يجب فصل طبقة Extraction عن Transformation؟**
لأن لكل طبقة مسؤولية مختلفة تمامًا: الاستخراج يتعامل مع تفاصيل الاتصال بالمصدر (ملف، HTTP، SQL) وأخطائه الخاصة، بينما التحويل يتعامل مع منطق العمل (Business Logic) لتنظيف البيانات وتوحيدها. فصلهما يجعل كل طبقة قابلة للاختبار والتعديل بشكل مستقل — يمكن تغيير مصدر البيانات (من CSV إلى Excel مثلاً) دون التأثير على منطق التحويل إطلاقًا، والعكس صحيح.

**9. لماذا يعتبر Data Validation جزءًا أساسيًا من هندسة البيانات؟**
لأن جودة أي تحليل أو نموذج ذكاء اصطناعي محكومة بجودة البيانات التي بُني عليها ("Garbage In, Garbage Out"). التحقق من البيانات هو خط الدفاع الذي يمنع وصول قيم غير منطقية (عمر 150، معدل تراكمي 4.8) إلى المراحل التالية، ويحوّل مشاكل الجودة من أخطاء صامتة مكتشَفة متأخرًا إلى قواعد صريحة موثقة يمكن قياسها وتتبعها.

**10. كيف يمكن تطوير Pipeline ليعمل بشكل دوري وآلي؟**
عبر جدولته باستخدام أداة Orchestration مثل Apache Airflow أو Prefect، أو حتى عبر Cron Job بسيط يستدعي `main.py` على فترات محددة. الخطوة التالية المنطقية هي إضافة Incremental Processing (معالجة السجلات الجديدة/المعدّلة فقط بالاعتماد على timestamp أو معرّف تشغيل سابق) بدلًا من إعادة معالجة كامل البيانات في كل مرة، مع تنبيهات آلية عند فشل أي مرحلة.

**11. كيف يمكن جعل Pipeline يتعامل مع ملايين السجلات؟**
باستبدال pandas (الذي يحمّل كل البيانات في الذاكرة) بأدوات معالجة موزّعة أو تدفقية مثل Apache Spark أو Dask للمعالجة المتوازية عبر عدة أجهزة، وقراءة البيانات على دفعات (Chunking) بدلًا من تحميلها دفعة واحدة، بالإضافة إلى تخزين الناتج في صيغة عمودية مضغوطة مثل Parquet بدلًا من CSV، ونقل قواعد التحقق والتحويل لتُنفَّذ داخل قاعدة البيانات أو محرك المعالجة نفسه بدلًا من الذاكرة المحلية.

**12. ما الفرق بين Batch Processing و Streaming Processing؟**
Batch Processing يعالج البيانات على شكل دفعات كبيرة بعد تجميعها خلال فترة زمنية (مثل تشغيل هذا الـ Pipeline مرة يوميًا على كل بيانات اليوم) — مناسب عندما لا تكون الفورية مطلوبة. أما Streaming Processing فيعالج كل سجل أو حدث فور وصوله بشكل مستمر ولحظي (مثل معالجة معاملات مالية أو نقرات مستخدمين في الوقت الفعلي) — مناسب عندما تكون سرعة الاستجابة والتحديث اللحظي أمرًا حاسمًا.
