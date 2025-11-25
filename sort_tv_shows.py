##!/usr/bin/env python3
# Clean, efficient standalone script — no imports.
# Reads CSV, computes show runtimes in days, sorts them, and writes new CSV.

CSV_IN = r"c:/Users/sebas/Downloads/TV_show_data.csv"
CSV_OUT = r"c:/Users/sebas/Downloads/TV_show_ordered_by_runtime.csv"

# Fallback end date for shows still running
FALLBACK_TODAY = (2025, 11, 24)



def split_csv_line(line):
    """Minimal CSV parser handling quoted fields with escaped quotes."""
    fields = []
    field = ""
    in_quotes = False
    i = 0

    while i < len(line):
        ch = line[i]

        if ch == '"':
            # Escaped quote ("")
            if in_quotes and i + 1 < len(line) and line[i+1] == '"':
                field += '"'
                i += 2
                continue
            # Toggle quoting state
            in_quotes = not in_quotes
            i += 1
            continue

        if ch == "," and not in_quotes:
            fields.append(field)
            field = ""
            i += 1
            continue

        field += ch
        i += 1

    fields.append(field.rstrip("\n").rstrip("\r"))
    return fields

def parse_date(s):
    """Parses M/D/YYYY. Returns (y,m,d) or None."""
    if not s:
        return None
    s = s.strip()
    if not s:
        return None

    parts = s.split("/")
    if len(parts) != 3:
        return None

    try:
        month = int(parts[0])
        day = int(parts[1])
        year = int(parts[2])
    except:
        return None

    return (year, month, day)


def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def days_since_epoch(y, m, d):
    """Convert date to a serial day number (Gregorian)."""
    mdays = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Days for complete prior years
    years = y - 1
    days = years * 365 + years // 4 - years // 100 + years // 400

    # Add months this year
    for mm in range(1, m):
        days += mdays[mm - 1]
        if mm == 2 and is_leap(y):
            days += 1

    return days + d


def day_diff(start, end):
    """Compute difference in days between two (y,m,d) tuples."""
    if not start or not end:
        return None
    return days_since_epoch(*end) - days_since_epoch(*start)


def main():
    try:
        f = open(CSV_IN, "r", encoding="utf-8")
    except Exception as e:
        print("Error opening input file:", e)
        return

    lines = f.readlines()
    f.close()

    if not lines:
        print("Input CSV is empty.")
        return

    # ---- Parse Header ----
    header = split_csv_line(lines[0])
    header_norm = [h.strip().lower() for h in header]

    def find_col(keyword):
        for idx, h in enumerate(header_norm):
            if keyword in h:
                return idx
        return None

    idx_name = find_col("name")
    idx_prem = find_col("premiere")
    idx_end = find_col("end")

    if None in (idx_name, idx_prem, idx_end):
        print("Error: Header missing Name, Premiere Date, or End Date.")
        return

    # ---- Process Rows ----
    show_to_runtime = {}

    for line in lines[1:]:
        if not line.strip():
            continue

        fields = split_csv_line(line)

        if idx_name >= len(fields):
            continue

        name = fields[idx_name].strip()
        prem_str = fields[idx_prem].strip() if idx_prem < len(fields) else ""
        end_str = fields[idx_end].strip() if idx_end < len(fields) else ""

        start_date = parse_date(prem_str)
        end_date = parse_date(end_str) or FALLBACK_TODAY

        if not start_date:
            continue

        runtime = day_diff(start_date, end_date)
        if runtime is None:
            continue

        # If duplicate show appears, keep longest runtime
        if name not in show_to_runtime or runtime > show_to_runtime[name]:
            show_to_runtime[name] = runtime

    # ---- Sort by runtime ----
    ordered = sorted(show_to_runtime.items(), key=lambda x: x[1], reverse=True)

    # ---- Write Output ----
    try:
        out = open(CSV_OUT, "w", encoding="utf-8")
    except Exception as e:
        print("Error writing output file:", e)
        return

    out.write("Name,RunDays\n")
    for name, days in ordered:
        # Quote names with commas or quotes
        if '"' in name:
            name = '"' + name.replace('"', '""') + '"'
        elif "," in name:
            name = f'"{name}"'

        out.write(f"{name},{days}\n")

    out.close()

    print(f"Wrote {CSV_OUT} with {len(ordered)} unique shows.")


if __name__ == "__main__":
    main()
