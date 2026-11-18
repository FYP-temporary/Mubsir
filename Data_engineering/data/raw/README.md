# Raw Data

The original **CERT Insider Threat Dataset r6.2** is not included in this repository because of its large size.

To rebuild the data engineering pipeline from the original source data, obtain the CERT r6.2 dataset separately and place it under:

```text
data/raw/r6.2/
```

The expected raw data includes the main activity files:

```text
email.csv
file.csv
http.csv
logon.csv
device.csv
```

and the required r6.2 ground-truth files under:

```text
data/raw/r6.2/answers/
```

For dataset source information, required files, and acquisition details, see:

```text
docs/DATASET_SOURCE.md
```