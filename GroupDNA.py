import os
import sys
from datetime import datetime, timedelta
import numpy as np

LINE = "=" * 72
SUBLINE = "-" * 72
GROUP_NAME_FALLBACK = "Group Chat"

STOP_WORDS = {
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "it", "they",
    "is", "am", "are", "was", "were", "be", "been", "being", "the", "a",
    "an", "and", "or", "to", "of", "in", "on", "for", "from", "at", "by",
    "with", "this", "that", "these", "those", "there", "here", "so", "but",
    "if", "then", "than", "as", "not", "no", "yes", "ok", "okay", "hai",
    "h", "ka", "ke", "ki", "ko", "se", "na", "toh", "aur", "ho", "tha",
    "thi", "hu", "hain", "just", "can", "will", "what", "when", "where",
}

PUNCTUATION = ".,!?;:\"'()[]{}<>/\\|@#$%^&*_+=~`…“”‘’-"

CARE_PHRASES = [
    "okay", "safe", "eat", "sleep", "take care", "are you", "please",
    "reminder", "drink water", "don't forget", "dont forget",
]

FUNNY_WORDS = ["lol", "lmao", "haha", "rofl", "lmfao"]


class ReportWriter:
    def __init__(self, console):
        self.console = console
        self.parts = []

    def write(self, text):
        self.console.write(text)
        self.parts.append(text)

    def flush(self):
        self.console.flush()

    def text(self):
        return "".join(self.parts)


def title(text):
    print()
    print(LINE)
    print(text.center(72))
    print(LINE)


def subtitle(text):
    print()
    print(text)
    print("-" * len(text))


def first_name(full_name):
    parts = full_name.strip().split()
    return parts[0] if parts else full_name


def is_date_start(line):
    if len(line) < 8:
        return False

    return (
        line[0].isdigit()
        and line[1].isdigit()
        and line[2] == "/"
        and line[3].isdigit()
        and line[4].isdigit()
        and line[5] == "/"
        and line[6].isdigit()
        and line[7].isdigit()
    )

def convert_to_24_hour(timestamp):
    timestamp = timestamp.replace("\u202f", " ").replace("\xa0", " ")
    timestamp = " ".join(timestamp.split())

    date_part, time_part = timestamp.split(", ")
    time_value, period = time_part.split(" ")

    hour, minute = time_value.split(":")
    hour = int(hour)

    period = period.lower()

    if period == "pm" and hour != 12:
        hour += 12

    if period == "am" and hour == 12:
        hour = 0

    return f"{date_part}, {hour:02d}:{minute}"
def parse_datetime(timestamp):
    if "am" in timestamp.lower() or "pm" in timestamp.lower():
        timestamp = convert_to_24_hour(timestamp)

    return datetime.strptime(timestamp, "%d/%m/%y, %H:%M")


def clean_word(word):
    return word.lower().strip(PUNCTUATION)


def extract_words(text):
    words = []

    for raw_word in text.split():
        word = clean_word(raw_word)

        if word == "":
            continue

        if word in STOP_WORDS:
            continue

        words.append(word)

    return words


def ask_for_file():
    while True:
        file_name = input("Enter the full path to the WhatsApp chat file (.txt): ").strip()
        file_name = file_name.strip('"').strip("'")

        if os.path.isfile(file_name):
            return file_name

        print()
        print("File not found. Please enter a valid full file path.")
        print()


def read_lines(file_name):
    with open(file_name, "r", encoding="utf-8") as file:
        return file.readlines()


def report_file_name(chat_file_name):
    folder = os.path.dirname(chat_file_name)
    base_name = os.path.basename(chat_file_name)
    name_without_extension = os.path.splitext(base_name)[0]
    return os.path.join(folder, f"GroupDNA_Report_{name_without_extension}.txt")


def save_report(report_text, output_file_name):
    with open(output_file_name, "w", encoding="utf-8") as file:
        file.write(report_text)


def parse_chat(lines):
    messages = []
    participants = set()
    stats = {
        "system_messages": 0,
        "media_messages": 0,
        "deleted_messages": 0,
    }
    media_counter = {}
    deleted_counter = {}
    group_name = GROUP_NAME_FALLBACK
    previous_message = None

    for raw_line in lines:
        line = raw_line.strip()

        if line == "":
            continue

        if not is_date_start(line):
            if previous_message is not None:
                previous_message["text"] += "\n" + line
            continue

        if " - " not in line:
            continue

        timestamp, rest = line.split(" - ", 1)

        if ": " not in rest:
            stats["system_messages"] += 1

            if "created group" in rest and '"' in rest:
                pieces = rest.split('"')
                if len(pieces) >= 2:
                    group_name = pieces[1]

            previous_message = None
            continue

        sender, text = rest.split(": ", 1)

        try:
            dt = parse_datetime(timestamp)
        except ValueError:
            continue

        is_media = text == "<Media omitted>"
        is_deleted = text == "This message was deleted"

        if is_media:
            stats["media_messages"] += 1
            media_counter[sender] = media_counter.get(sender, 0) + 1

        if is_deleted:
            stats["deleted_messages"] += 1
            deleted_counter[sender] = deleted_counter.get(sender, 0) + 1

        participants.add(sender)

        message = {
            "datetime": dt,
            "timestamp": timestamp,
            "sender": sender,
            "text": text,
            "media": is_media,
            "deleted": is_deleted,
        }

        messages.append(message)
        previous_message = message

    messages.sort(key=lambda item: item["datetime"])

    return messages, participants, stats, media_counter, deleted_counter, group_name


def count_messages(messages):
    counts = {}

    for message in messages:
        sender = message["sender"]
        counts[sender] = counts.get(sender, 0) + 1

    return counts


def sorted_count_items(counts):
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)


def marker(value, maximum, width=22):


    size = int((value / maximum) * width)
    if size < 1:
        size = 1

    return "*" * size


def format_duration(seconds):
    if seconds is None:
        return "N/A"

    minutes = seconds / 60

    if minutes < 60:
        return f"{minutes:.1f} minutes"

    hours = minutes / 60

    if hours < 48:
        return f"{hours:.1f} hours"

    return f"{hours / 24:.1f} days"


def build_daily_activity(messages):
    daily = {}

    for message in messages:
        day = message["datetime"].date()
        daily[day] = daily.get(day, 0) + 1

    return daily


def build_hour_activity(messages):
    hourly = {}

    for hour in range(24):
        hourly[hour] = 0

    for message in messages:
        hourly[message["datetime"].hour] += 1

    return hourly


def build_msgtrace(messages, user_list):
    msgtrace = np.zeros((len(user_list), 24), dtype=int)
    user_index = {}

    for index, user in enumerate(user_list):
        user_index[user] = index

    for message in messages:
        row = user_index[message["sender"]]
        col = message["datetime"].hour
        msgtrace[row][col] += 1

    return msgtrace


def top_words(messages, sender=None, limit=10):
    counts = {}

    for message in messages:
        if sender is not None and message["sender"] != sender:
            continue

        if message["media"] or message["deleted"]:
            continue

        for word in extract_words(message["text"]):
            counts[word] = counts.get(word, 0) + 1

    return sorted_count_items(counts)[:limit]


def response_times(messages, participants):
    gaps_by_user = {}

    for user in participants:
        gaps_by_user[user] = []

    for index in range(1, len(messages)):
        previous = messages[index - 1]
        current = messages[index]

        if previous["sender"] == current["sender"]:
            continue

        gap = (current["datetime"] - previous["datetime"]).total_seconds()

        if gap >= 0:
            gaps_by_user[current["sender"]].append(gap)

    averages = {}

    for user in participants:
        gaps = gaps_by_user[user]
        averages[user] = None if len(gaps) == 0 else sum(gaps) / len(gaps)

    return averages


def silent_streaks(messages, participants, first_date, last_date):
    all_dates = []
    day = first_date.date()

    while day <= last_date.date():
        all_dates.append(day)
        day += timedelta(days=1)

    streaks = {}
    ranges = {}

    for user in participants:
        active_days = set()

        for message in messages:
            if message["sender"] == user:
                active_days.add(message["datetime"].date())

        longest = 0
        current = 0
        current_start = None
        best_start = None
        best_end = None

        for day in all_dates:
            if day in active_days:
                if current > longest:
                    longest = current
                    best_start = current_start
                    best_end = day - timedelta(days=1)
                current = 0
                current_start = None
            else:
                if current == 0:
                    current_start = day
                current += 1

        if current > longest:
            longest = current
            best_start = current_start
            best_end = all_dates[-1]

        streaks[user] = longest
        ranges[user] = (best_start, best_end)

    return streaks, ranges


def burst_scores(messages, participants):
    burst_sum = {}
    burst_count = {}

    for user in participants:
        burst_sum[user] = 0
        burst_count[user] = 0

    if not messages:
        return {user: 0 for user in participants}

    current_sender = messages[0]["sender"]
    current_burst = 1

    for message in messages[1:]:
        if message["sender"] == current_sender:
            current_burst += 1
        else:
            burst_sum[current_sender] += current_burst
            burst_count[current_sender] += 1
            current_sender = message["sender"]
            current_burst = 1

    burst_sum[current_sender] += current_burst
    burst_count[current_sender] += 1

    scores = {}

    for user in participants:
        if burst_count[user] == 0:
            scores[user] = 0
        else:
            scores[user] = burst_sum[user] / burst_count[user]

    return scores


def average_words_per_message(messages, participants):
    total_words = {}
    counts = {}

    for user in participants:
        total_words[user] = 0
        counts[user] = 0

    for message in messages:
        if message["media"] or message["deleted"]:
            continue

        sender = message["sender"]
        total_words[sender] += len(message["text"].split())
        counts[sender] += 1

    averages = {}

    for user in participants:
        averages[user] = total_words[user] / counts[user] if counts[user] else 0

    return averages


def phrase_count_score(messages, participants, phrases):
    scores = {}

    for user in participants:
        scores[user] = 0

    for message in messages:
        if message["media"] or message["deleted"]:
            continue

        text = message["text"].lower()

        for phrase in phrases:
            if phrase in text:
                scores[message["sender"]] += 1

    return scores


def drama_scores(messages, participants):
    drama = {}
    total = {}

    for user in participants:
        drama[user] = 0
        total[user] = 0

    for message in messages:
        if message["media"] or message["deleted"]:
            continue

        sender = message["sender"]
        text = message["text"].strip()
        total[sender] += 1

        if len(text) > 3 and (text.isupper() or text.count("!") >= 2):
            drama[sender] += 1

    scores = {}

    for user in participants:
        scores[user] = drama[user] / total[user] if total[user] else 0

    return scores


def funny_scores(messages, participants):
    funny = {}
    total = {}

    for user in participants:
        funny[user] = 0
        total[user] = 0

    for message in messages:
        if message["media"] or message["deleted"]:
            continue

        sender = message["sender"]
        total[sender] += 1
        text = message["text"].lower()

        for word in FUNNY_WORDS:
            if word in text:
                funny[sender] += 1
                break

    scores = {}

    for user in participants:
        scores[user] = funny[user] / total[user] if total[user] else 0

    return scores


def question_scores(messages, participants):
    questions = {}
    total = {}

    for user in participants:
        questions[user] = 0
        total[user] = 0

    for message in messages:
        if message["media"] or message["deleted"]:
            continue

        sender = message["sender"]
        total[sender] += 1

        if message["text"].strip().endswith("?"):
            questions[sender] += 1

    scores = {}

    for user in participants:
        scores[user] = questions[user] / total[user] if total[user] else 0

    return scores


def night_scores(msgtrace, user_list):
    scores = {}

    for index, user in enumerate(user_list):
        total = int(np.sum(msgtrace[index]))
        night = int(np.sum(msgtrace[index][23:24]) + np.sum(msgtrace[index][0:5]))
        scores[user] = night / total if total else 0

    return scores


def assign_archetypes(messages, participants, msgtrace, user_list, silent_streak, total_days):
    burst = burst_scores(messages, participants)
    mom = phrase_count_score(messages, participants, CARE_PHRASES)
    night = night_scores(msgtrace, user_list)
    storyteller = average_words_per_message(messages, participants)
    drama = drama_scores(messages, participants)
    comedy = funny_scores(messages, participants)
    questions = question_scores(messages, participants)
    ghost = {}

    for user in participants:
        ghost[user] = silent_streak[user] / total_days if total_days else 0


    raw_scores = {}

    for user in participants:
        raw_scores[user] = {
            "THE SPAMMER": burst[user] / 3,
            "THE GROUP MOM": mom[user] / max(1, max(mom.values())),
            "THE NIGHT OWL": night[user] / 0.60,
            "THE STORYTELLER": storyteller[user] / 30,
            "THE DRAMA QUEEN": drama[user] / 0.30,
            "THE GHOST": ghost[user] / 0.60,
            "THE COMEDIAN": comedy[user] / 0.20,
            "THE QUESTION MASTER": questions[user] / 0.25,
        }

    assigned = {}

    for user in participants:
        best_label = max(raw_scores[user], key=raw_scores[user].get)
        assigned[user] = best_label

    details = {}

    for user in participants:
        details[user] = {
            "THE SPAMMER": f"avg {burst[user]:.1f} msgs in a row",
            "THE GROUP MOM": f"caring keyword score: {mom[user]}",
            "THE NIGHT OWL": f"{night[user] * 100:.1f}% msgs between 23h-04h",
            "THE STORYTELLER": f"avg {storyteller[user]:.1f} words per msg",
            "THE DRAMA QUEEN": f"{drama[user] * 100:.1f}% dramatic messages",
            "THE GHOST": f"silent on {silent_streak[user]} of {total_days} days",
            "THE COMEDIAN": f"{comedy[user] * 100:.1f}% funny-word messages",
            "THE QUESTION MASTER": f"{questions[user] * 100:.1f}% questions",
        }

    score_tables = {
        "burst": burst,
        "mom": mom,
        "night": night,
        "storyteller": storyteller,
        "drama": drama,
        "ghost": ghost,
        "comedy": comedy,
        "questions": questions,
    }

    return assigned, details, score_tables


def print_parser_summary(messages, participants, stats, first_date, last_date):
    title("PARSER SUMMARY")
    print(f"Messages parsed       : {len(messages):,}")
    print(f"Participants          : {len(participants)}")
    print(f"System messages       : {stats['system_messages']}")
    print(f"Media messages        : {stats['media_messages']}")
    print(f"Deleted messages      : {stats['deleted_messages']}")

    if first_date is not None and last_date is not None:
        print(f"First message         : {first_date.strftime('%d %B %Y, %H:%M')}")
        print(f"Last message          : {last_date.strftime('%d %B %Y, %H:%M')}")


def print_group_overview(group_name, first_date, last_date, total_days, messages, participants, counts):
    title("GROUP OVERVIEW")
    print(f"Group                 : {group_name}")
    print(f"Period                : {first_date.strftime('%d %B %Y')} to {last_date.strftime('%d %B %Y')} ({total_days} days)")
    print(f"Total messages        : {len(messages):,}")
    print(f"Participants          : {len(participants)}")

    subtitle("MESSAGES PER PERSON")
    maximum = max(counts.values()) if counts else 0

    for user, count in sorted_count_items(counts):
        percent = (count / len(messages)) * 100 if messages else 0
        print(f"{user:<9} {marker(count, maximum):<22} {count:>5,}  ({percent:>4.1f}%)")


def print_activity(daily, hourly, total_days):
    title("CHAT ACTIVITY")
    busiest_day = max(daily, key=daily.get)
    busiest_hour = max(hourly, key=hourly.get)
    average_per_day = hourly[busiest_hour] / total_days if total_days else 0

    print(f"Busiest day           : {busiest_day.strftime('%d %B %Y')} ({daily[busiest_day]} messages)")
    print(f"Busiest hour          : {busiest_hour:02d}:00 - {(busiest_hour + 1) % 24:02d}:00 ({hourly[busiest_hour]} messages, avg {average_per_day:.1f}/day)")

    subtitle("TOP 10 BUSIEST DAYS")
    for day, count in sorted_count_items(daily)[:10]:
        print(f"{day.strftime('%d %b %Y')} : {count}")


def print_top_words(messages):
    title("THIS GROUP'S FAVOURITE WORDS")
    words = top_words(messages, limit=10)
    maximum = words[0][1] if words else 0

    for word, count in words:
        print(f"{word:<12} {marker(count, maximum):<22} {count}")


def print_response_patterns(averages, silent, ranges):
    title("RESPONSE PATTERNS")
    valid = {}

    for user, seconds in averages.items():
        if seconds is not None:
            valid[user] = seconds

    if valid:
        fastest = min(valid, key=valid.get)
        slowest = max(valid, key=valid.get)
        print(f"Fastest replier       : {fastest:<9} (avg {format_duration(valid[fastest])})")
        print(f"Slowest replier       : {slowest:<9} (avg {format_duration(valid[slowest])})")

    subtitle("AVERAGE RESPONSE TIME")
    for user, seconds in sorted(averages.items()):
        print(f"{user:<9} : {format_duration(seconds)}")

    subtitle("LONGEST SILENT STREAKS")
    for user, days in sorted_count_items(silent):
        start, end = ranges[user]

        if days == 0 or start is None or end is None:
            print(f"{user:<9} : {days:>2} days")
        else:
            print(f"{user:<9} : {days:>2} days ({start.strftime('%d %b')} - {end.strftime('%d %b')})")


def print_media_deleted(participants, media_counter, deleted_counter):
    title("MEDIA AND DELETED MESSAGES")
    print(f"{'Name':<10}{'Media':>8}{'Deleted':>10}")
    print(SUBLINE[:28])

    for user in sorted(participants):
        media = media_counter.get(user, 0)
        deleted = deleted_counter.get(user, 0)
        print(f"{first_name(user):<10}{media:>8}{deleted:>10}")


def print_archetypes(user_list, assigned, details, score_tables):
    title("PERSONALITY ARCHETYPES")

    for user in user_list:
        label = assigned[user]
        name = first_name(user)
        print(f"{name:<12} -> {label:<20} ({details[user][label]})")

    subtitle("ARCHETYPE SCORES")
    print(f"{'Name':<12}{'Burst':>8}{'Mom':>8}{'Night':>9}{'Story':>9}{'Drama':>9}{'Ghost':>9}")
    print(SUBLINE[:61])

    for user in user_list:
        name = first_name(user)
        print(
            f"{name:<12}"
            f"{score_tables['burst'][user]:>8.2f}"
            f"{score_tables['mom'][user]:>8}"
            f"{score_tables['night'][user] * 100:>8.1f}%"
            f"{score_tables['storyteller'][user]:>9.1f}"
            f"{score_tables['drama'][user] * 100:>8.1f}%"
            f"{score_tables['ghost'][user] * 100:>8.1f}%"
        )


def run_report():
    file_name = ask_for_file()
    lines = read_lines(file_name)
    messages, participants, stats, media_counter, deleted_counter, group_name = parse_chat(lines)

    if not messages:
        print("No valid WhatsApp messages found in this file.")
        return

    first_date = messages[0]["datetime"]
    last_date = messages[-1]["datetime"]
    total_days = (last_date.date() - first_date.date()).days + 1
    counts = count_messages(messages)
    user_list = [user for user, count in sorted_count_items(counts)]
    daily = build_daily_activity(messages)
    hourly = build_hour_activity(messages)
    msgtrace = build_msgtrace(messages, user_list)
    averages = response_times(messages, participants)
    silent, silent_ranges = silent_streaks(messages, participants, first_date, last_date)
    assigned, details, score_tables = assign_archetypes(
        messages, participants, msgtrace, user_list, silent, total_days
    )

    original_stdout = sys.stdout
    report_writer = ReportWriter(original_stdout)
    sys.stdout = report_writer

    try:
        title(f'GroupDNA REPORT  -  "{group_name}"')
        print(f"{total_days} days  |  {len(messages):,} messages  |  {len(participants)} members")

        print_parser_summary(messages, participants, stats, first_date, last_date)
        print_group_overview(group_name, first_date, last_date, total_days, messages, participants, counts)
        print_activity(daily, hourly, total_days)

        print_top_words(messages)
        print_response_patterns(averages, silent, silent_ranges)
        print_media_deleted(participants, media_counter, deleted_counter)
        print_archetypes(user_list, assigned, details, score_tables)

        print()
        print(LINE)
    finally:
        sys.stdout = original_stdout

    output_file_name = report_file_name(file_name)
    save_report(report_writer.text(), output_file_name)
    print()
    print(f"Report saved to: {output_file_name}")

run_report()
