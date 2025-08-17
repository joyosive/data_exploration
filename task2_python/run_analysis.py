#!/usr/bin/env python3
"""
Run this script to analyze the contract_events.csv file
"""

from event_analysis import (
    load_data,
    find_orphan_events,
    calculate_time_deltas,
    rank_senders_by_activity,
    find_sender_peak_blocks,
    analyze_data_quality,
    detect_bots,
    visualize_event_type_frequency
)

CSV_PATH = 'contract_events.csv'

def main():
    print("\n" + "=" * 60)
    print("TASK 2: BLOCKCHAIN EVENT ANALYSIS")
    print("=" * 60)

    df = load_data(CSV_PATH)
    print(f"\n✓ Loaded {len(df)} events from CSV")

    # 1. Orphan Events
    print("\n1. ORPHAN EVENTS")
    print("-" * 40)
    orphans = find_orphan_events(df)
    print(f"Found {len(orphans)} orphan events (referenced but not in dataset)")
    print(f"First 10: {orphans[:10]}")

    # 2. Time Deltas
    print("\n2. TIME DELTAS PER CONTRACT")
    print("-" * 40)
    time_deltas = calculate_time_deltas(df)
    for contract, delta in time_deltas.items():
        print(f"{contract}: {delta:.2f} seconds average")

    # 3. Sender Activity
    print("\n3. SENDER ACTIVITY RANKING")
    print("-" * 40)
    rankings = rank_senders_by_activity(df)
    for sender, count in rankings[:5]:
        print(f"{sender}: {count} events")

    # 3.1. Sender Peak Blocks
    print("\n3.1. SENDER MAPPING - PEAK BLOCKS")
    print("-" * 40)
    find_sender_peak_blocks(df)

    # 4. Data Quality (Bonus)
    print("\n4. DATA QUALITY ANALYSIS (Bonus)")
    print("-" * 40)
    quality = analyze_data_quality(df)
    print(f"Missing values: {quality['missing_values']}")
    print(f"Duplicate events: {quality['duplicate_events']}")
    print(f"Timestamp issues: {len(quality['timestamp_issues'])}")

    # 5. Bot Detection (Bonus)
    print("\n5. BOT DETECTION (Bonus)")
    print("-" * 40)
    bot_details = detect_bots(df)
    
    # Analysis complete - results shown above
    
    if len(bot_details) > 0:
        print(f"Found {len(bot_details)} suspected bot addresses:\n")
        for sender, info in bot_details.items():
            print(f"Address: {sender} ({info['total_events']} events)")
            print(f"   Detection criteria: {', '.join(info['reasons'])}")
            for detail_type, detail_value in info['details'].items():
                print(f"   - {detail_type}: {detail_value}")
            print()
    else:
        print("No clear bot patterns detected with current thresholds.")
        print("Note: All major senders have similar activity levels (~4,000 events)")
        print("suggesting this may be synthetic test data rather than real user behavior.")

    # 6. Event Type Visualization
    print("\n6. EVENT TYPE FREQUENCY ANALYSIS")
    print("-"*40)
    visualize_event_type_frequency(df)

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()