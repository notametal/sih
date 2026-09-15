"""
Generates a placeholder drying-run dataset shaped like what the Arduino
logs:

temperature, humidity, humidity_change, temperature_change,
elapsed_time -> label

label:
0 = not done
1 = drying complete

Replace this with real Arduino data as soon as you have it.
The real CSV should use the same column names.
"""

import csv
import random

random.seed(42)

rows = []

N_RUNS = 40
SECONDS_PER_RUN = 1200   # 20 minutes, one reading/sec

for run in range(N_RUNS):

    # Initial conditions
    temp = random.uniform(30.0, 36.0)
    humidity = random.uniform(72.0, 88.0)

    prev_temp = temp
    prev_hum = humidity

    # Each drying session behaves slightly differently
    hum_decay = random.uniform(0.035, 0.075)
    temp_drift = random.uniform(-0.003, 0.008)

    # More realistic completion humidity
    dry_threshold = random.uniform(35.0, 45.0)

    # Require some minimum drying time
    minimum_dry_time = random.randint(400, 700)

    for t in range(SECONDS_PER_RUN):

        # -------------------------------------------------
        # Simulate humidity falling during drying
        # -------------------------------------------------

        # Drying slows down as humidity becomes lower
        slowdown = max(0.25, humidity / 90.0)

        humidity -= hum_decay * slowdown

        # Sensor/environment noise
        humidity += random.uniform(-0.10, 0.10)

        humidity = max(20.0, min(95.0, humidity))

        # -------------------------------------------------
        # Simulate temperature
        # -------------------------------------------------

        temp += temp_drift
        temp += random.uniform(-0.04, 0.04)

        temp = max(20.0, min(60.0, temp))

        # -------------------------------------------------
        # Calculate changes
        # -------------------------------------------------

        humidity_change = humidity - prev_hum
        temperature_change = temp - prev_temp

        # -------------------------------------------------
        # Drying-complete label
        # -------------------------------------------------

        # Done only if:
        # 1. humidity is sufficiently low
        # 2. enough time has passed
        #
        # Later, real data should determine this logic.
        label = int(
            humidity <= dry_threshold
            and t >= minimum_dry_time
        )

        rows.append([
            round(temp, 2),
            round(humidity, 2),
            round(humidity_change, 3),
            round(temperature_change, 3),
            t,
            label,
        ])

        prev_temp = temp
        prev_hum = humidity


# -------------------------------------------------
# Write CSV
# -------------------------------------------------

with open("sample_data.csv", "w", newline="") as f:

    writer = csv.writer(f)

    writer.writerow([
        "temperature",
        "humidity",
        "humidity_change",
        "temperature_change",
        "elapsed_time",
        "label",
    ])

    writer.writerows(rows)


print(f"Wrote {len(rows)} rows to sample_data.csv")

# -------------------------------------------------
# Show label distribution
# -------------------------------------------------

zeros = sum(row[-1] == 0 for row in rows)
ones = sum(row[-1] == 1 for row in rows)

print(f"Not complete (0): {zeros}")
print(f"Complete     (1): {ones}")

print(
    f"Complete percentage: "
    f"{(ones / len(rows)) * 100:.2f}%"
)