
from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)
DATABASE = "accessibility.db"

FEATURES = ["Ramp", "Lift", "Accessible Toilet", "Parking"]

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Public Facility Accessibility Assessment</title>

<style>
* { box-sizing: border-box; }

body {
    margin: 0;
    padding: 25px;
    font-family: Arial, sans-serif;
    background: #eef2f7;
    color: #263445;
}

.container {
    max-width: 850px;
    margin: auto;
    padding: 28px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 15px #00000012;
}

h1, h2 { color: #174a7e; }

.subtitle { color: #586779; }

label {
    display: block;
    margin-top: 12px;
    font-weight: bold;
}

input, select, textarea {
    width: 100%;
    padding: 11px;
    margin-top: 6px;
    border: 1px solid #ccd5df;
    border-radius: 5px;
    background: white;
}

button {
    width: 100%;
    padding: 12px;
    margin-top: 20px;
    border: none;
    border-radius: 6px;
    background: #174a7e;
    color: white;
    font-size: 16px;
    cursor: pointer;
}

button:hover { background: #10375d; }

.feature {
    margin-top: 18px;
    padding: 15px;
    border: 1px solid #dce3eb;
    border-radius: 8px;
    background: #f8fafc;
}

.message {
    padding: 12px;
    background: #e4f7e9;
    border-radius: 6px;
    color: #17632e;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

th, td {
    padding: 10px;
    border: 1px solid #dce3eb;
    text-align: left;
}

th { background: #eaf1f8; }

.small { color: #586779; font-size: 13px; }

@media(max-width: 600px) {
    body { padding: 10px; }
    .container { padding: 16px; }
}
</style>
</head>

<body>
<div class="container">

<h1>Public Facility Accessibility Assessment</h1>
<p class="subtitle">
Evaluate ramps, lifts, accessible toilets and designated parking
at public facilities.
</p>

{% if message %}
<p class="message">{{ message }}</p>
{% endif %}

<form method="POST">

<h2>Facility Information</h2>

<label>Facility Name</label>
<input type="text" name="facility" required>

<label>Facility Type</label>
<select name="kind" required>
<option value="Hospital">Hospital</option>
<option value="College">College</option>
<option value="Shopping Mall">Shopping Mall</option>
<option value="Railway Station">Railway Station</option>
<option value="Government Office">Government Office</option>
<option value="Other">Other</option>
</select>

<label>Assessor Name</label>
<input type="text" name="assessor" required>

<h2>Accessibility Features</h2>

{% for feature in features %}
<div class="feature">
    <h3>{{ feature }}</h3>

    <label>Availability</label>
    <select name="{{ feature }}_availability">
        <option value="Available">Available</option>
        <option value="Not Available">Not Available</option>
    </select>

    <label>Usability</label>
    <select name="{{ feature }}_usability">
        <option value="Usable">Usable</option>
        <option value="Not Usable">Not Usable</option>
    </select>
</div>
{% endfor %}

<label>Observations / Accessibility Problems</label>
<textarea name="observations" rows="4"
placeholder="Describe barriers or improvement suggestions..."></textarea>

<button type="submit">Save Assessment</button>
</form>

<h2>Assessment Results</h2>
<p class="small">
Percentages represent the share of the four assessed features.
</p>

{% if records %}
<table>
<thead>
<tr>
<th>Facility</th>
<th>Availability</th>
<th>Usability</th>
</tr>
</thead>
<tbody>
{% for record in records %}
<tr>
<td>{{ record[0] }}</td>
<td>{{ record[1] }}%</td>
<td>{{ record[2] }}%</td>
</tr>
{% endfor %}
</tbody>
</table>
{% else %}
<p>No assessments have been saved yet.</p>
{% endif %}

</div>
</body>
</html>
"""


def initialize_database():
    with sqlite3.connect(DATABASE) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility TEXT NOT NULL,
                facility_type TEXT NOT NULL,
                assessor TEXT NOT NULL,
                ramp_availability TEXT,
                ramp_usability TEXT,
                lift_availability TEXT,
                lift_usability TEXT,
                toilet_availability TEXT,
                toilet_usability TEXT,
                parking_availability TEXT,
                parking_usability TEXT,
                observations TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


@app.route("/", methods=["GET", "POST"])
def home():
    message = ""

    if request.method == "POST":
        values = []

        for feature in FEATURES:
            values.append(
                request.form.get(feature + "_availability", "Not Available")
            )
            values.append(
                request.form.get(feature + "_usability", "Not Usable")
            )

        with sqlite3.connect(DATABASE) as connection:
            connection.execute("""
                INSERT INTO assessments (
                    facility, facility_type, assessor,
                    ramp_availability, ramp_usability,
                    lift_availability, lift_usability,
                    toilet_availability, toilet_usability,
                    parking_availability, parking_usability,
                    observations
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form.get("facility", "").strip(),
                request.form.get("kind", ""),
                request.form.get("assessor", "").strip(),
                *values,
                request.form.get("observations", "").strip()
            ))

        message = "Assessment saved successfully!"

    records = []

    with sqlite3.connect(DATABASE) as connection:
        rows = connection.execute("""
            SELECT facility,
                   ramp_availability, ramp_usability,
                   lift_availability, lift_usability,
                   toilet_availability, toilet_usability,
                   parking_availability, parking_usability
            FROM assessments
            ORDER BY id DESC
        """).fetchall()

    for row in rows:
        facility = row[0]
        availability_values = [row[1], row[3], row[5], row[7]]
        usability_values = [row[2], row[4], row[6], row[8]]

        availability = round(
            availability_values.count("Available") / 4 * 100
        )
        usability = round(
            usability_values.count("Usable") / 4 * 100
        )

        records.append((facility, availability, usability))

    return render_template_string(
        HTML,
        features=FEATURES,
        records=records,
        message=message
    )


initialize_database()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
