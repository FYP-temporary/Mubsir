# Dataset Source

## Dataset

This project uses the **CERT Insider Threat Dataset r6.2**, developed by the CERT Division at Carnegie Mellon University.

The dataset contains simulated organizational activity generated for insider-threat research and includes multiple sources of user activity such as email, web, file, device, and logon events.

---

## Dataset Version

**CERT Insider Threat Dataset — Release 6.2**

The project specifically uses Release 6.2 because it provides activity types suitable for the three exfiltration channels studied in this project:

- External Email
- USB / Removable Media
- HTTP Upload

The dataset also includes official answer files describing known malicious-user scenarios.

---
## Official Source

The CERT Insider Threat Test Dataset is published by the
Software Engineering Institute (SEI), Carnegie Mellon University.

Official dataset page:

https://sei.cmu.edu/library/insider-threat-test-dataset/

Dataset DOI:

https://doi.org/10.1184/R1/12841247.v1

## Required Raw Files

The main raw files used by the data engineering pipeline are:

```text
email.csv
file.csv
http.csv
logon.csv
device.csv
```

The official CERT answer files used for ground-truth construction are:

```text
answers/insiders.csv
answers/r6.2-1.csv
answers/r6.2-2.csv
answers/r6.2-3.csv
answers/r6.2-4.csv
answers/r6.2-5.csv
```

---

## Expected Directory

After obtaining the CERT r6.2 dataset, place the raw files under:

```text
data/raw/r6.2/
```

The expected structure is:

```text
data/
└── raw/
    └── r6.2/
        ├── email.csv
        ├── file.csv
        ├── http.csv
        ├── logon.csv
        ├── device.csv
        └── answers/
            ├── insiders.csv
            ├── r6.2-1.csv
            ├── r6.2-2.csv
            ├── r6.2-3.csv
            ├── r6.2-4.csv
            └── r6.2-5.csv
```

---

## Repository Policy

The raw CERT r6.2 dataset is **not stored in this Git repository**.

The raw dataset is excluded because of its large size and should be obtained separately from the official dataset source.

The Git repository contains only the processed datasets, engineered features, notebooks, documentation, and pipeline code required for the project workflow.

---

## Data Usage

The dataset is used exclusively for academic and research purposes as part of the graduation project:

**AI-Based Detection of Cross-Channel Low-and-Slow Data Exfiltration Using UEBA**

All dataset use should follow the licensing and usage terms distributed with the CERT dataset.