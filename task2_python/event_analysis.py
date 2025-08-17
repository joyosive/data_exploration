from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


def load_data(file_path: str) -> pd.DataFrame:
    # Load CSV data
    df = pd.read_csv(file_path)
    # Convert timestamps to datetime
    df['block_timestamp'] = pd.to_datetime(df['block_timestamp'])
    return df


def find_orphan_events(df: pd.DataFrame) -> List[str]:
    orphan_events = []
    # Create lookup set
    all_events = set(df['event_id'])

    # Filter to events with previous refs
    events_with_previous = df[df['previous_event_id'].notna()]

    for _, row in events_with_previous.iterrows():
        # Check if referenced event exists
        if row['previous_event_id'] not in all_events:
            orphan_events.append(row['event_id'])

    return sorted(orphan_events)


def calculate_time_deltas(df: pd.DataFrame) -> Dict[str, float]:
    # Sort by contract then time
    df_sorted = df.sort_values(['contract_address', 'block_timestamp'])

    def calc_avg_delta(group):
        # Skip contracts with single events
        if len(group) <= 1:
            return 0.0
        # Calculate time differences
        time_diffs = group['block_timestamp'].diff().dropna()
        # Convert to seconds and average
        return time_diffs.dt.total_seconds().mean()

    time_deltas = df_sorted.groupby('contract_address').apply(calc_avg_delta, include_groups=False).to_dict()
    return time_deltas


def map_senders_to_contracts(df: pd.DataFrame) -> Dict[str, List[str]]:
    # Map each sender to their unique contracts
    sender_contracts = df.groupby('sender')['contract_address'].apply(lambda x: sorted(x.unique())).to_dict()
    return sender_contracts


def rank_senders_by_activity(df: pd.DataFrame) -> List[Tuple[str, int]]:
    # Count total events per sender
    sender_counts = df['sender'].value_counts()
    # Convert to list of tuples
    return list(sender_counts.items())


def find_sender_peak_blocks(df: pd.DataFrame) -> List[Tuple[str, int, int]]:
    """Find the block where each sender had the most events, ranked by frequency"""
    # Group by sender and block to get event counts
    sender_block_counts = df.groupby(['sender', 'block_number']).size().reset_index(name='event_count')
    
    # Find max count per sender
    max_counts_per_sender = sender_block_counts.groupby('sender')['event_count'].max().reset_index()
    max_counts_per_sender.columns = ['sender', 'max_event_count']
    
    # Get the blocks where max occurred
    peak_blocks = sender_block_counts.merge(
        max_counts_per_sender, 
        left_on=['sender', 'event_count'], 
        right_on=['sender', 'max_event_count']
    )
    
    # Take first occurrence if multiple blocks have same max count
    peak_blocks = peak_blocks.groupby('sender').first().reset_index()
    peak_blocks = peak_blocks[['sender', 'block_number', 'event_count']]
    
    # Sort by event count descending
    peak_blocks_sorted = peak_blocks.sort_values('event_count', ascending=False)

    print("Sender Mapping - Peak Blocks by Event Frequency:")
    print("=" * 60)
    # Table header
    print(f"{'Rank':<5} {'Sender':<42} {'Block Number':<12} {'Event Count':<12}")
    print("-" * 60)

    for rank, (sender, block_number, event_count) in enumerate(
            peak_blocks_sorted[['sender', 'block_number', 'event_count']].itertuples(index=False, name=None), 1):
        print(f"{rank:<5} {sender:<42} {block_number:<12} {event_count:<12}")

    # Return as list of tuples
    return list(peak_blocks_sorted[['sender', 'block_number', 'event_count']].itertuples(index=False, name=None))


def analyze_data_quality(df: pd.DataFrame) -> Dict:
    quality_report = {
        'total_records': len(df),
        'missing_values': {},
        'duplicate_events': 0,
        'invalid_statuses': [],
        'timestamp_issues': []
    }

    # Check for missing values across all columns
    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            quality_report['missing_values'][col] = missing_count

    # Count duplicate event IDs
    quality_report['duplicate_events'] = df['event_id'].duplicated().sum()

    # Expected status values
    valid_statuses = ['Confirmed', 'Pending', 'Reorged']
    # Find unexpected statuses
    invalid = df[~df['status'].isin(valid_statuses)]['status'].unique()
    # Convert to list if any found
    quality_report['invalid_statuses'] = list(invalid) if len(invalid) > 0 else []

    # Check for timestamp consistency issues
    df_sorted = df.sort_values('block_timestamp').reset_index(drop=True)
    if len(df_sorted) > 1:
        timestamp_issues = df_sorted[
            (df_sorted['block_timestamp'].shift(1) > df_sorted['block_timestamp']) &
            (df_sorted['block_number'].shift(1) < df_sorted['block_number'])
            ]
        quality_report['timestamp_issues'] = [
            {'event_id': row['event_id'], 'issue': 'timestamp_before_previous_block'}
            for _, row in timestamp_issues.iterrows()
        ]

    return quality_report


def detect_bots(df: pd.DataFrame) -> Dict[str, Dict]:
    bot_details = {}

    # Total block range for coverage calculations
    total_blocks = df['block_number'].max() - df['block_number'].min() + 1

    for sender in df['sender'].unique():
        if sender == '0x000000':  # Skip null address
            continue

        # Filter to current sender's events
        sender_data = df[df['sender'] == sender]
        reasons = []  # Bot detection criteria met
        details = {}  # Detailed metrics for this sender

        # Calculate block coverage ratio
        coverage = len(sender_data) / total_blocks
        if coverage > 0.1:
            reasons.append('unrealistic_coverage')
            # Store coverage details
            details['coverage'] = f"{coverage:.3f} events per block across {total_blocks:,} blocks"

        if len(sender_data) > 1000:
            # Check for suspiciously consistent activity patterns
            sender_sorted = sender_data.sort_values('block_number')
            # Divide activity into time periods
            n_periods = 10
            # Events per period
            period_size = len(sender_sorted) // n_periods
            # Store event count per period
            period_counts = []
            for i in range(n_periods):
                # Period start index
                start_idx = i * period_size
                # Period end, handle remainder
                end_idx = start_idx + period_size if i < n_periods - 1 else len(sender_sorted)
                # Count events in this period
                period_counts.append(end_idx - start_idx)
            activity_cv = np.std(period_counts) / np.mean(period_counts) if np.mean(period_counts) > 0 else 0

            if activity_cv < 0.1:
                reasons.append('perfectly_distributed_activity')
                details['activity_consistency'] = f"CV: {activity_cv:.3f} across time periods"

        # Calculate sender's active block range
        block_range = sender_data['block_number'].max() - sender_data['block_number'].min()
        # Events per block in sender's range
        sender_coverage_ratio = len(sender_data) / block_range if block_range > 0 else 0

        # Look for coordinated behavior with other senders
        similar_senders = 0
        for other_sender in df['sender'].unique():
            # Skip self and null address
            if other_sender != sender and other_sender != '0x000000':
                # Get other sender's data
                other_data = df[df['sender'] == other_sender]
                other_coverage = len(other_data) / total_blocks

                # Check for nearly identical patterns
                if (abs(len(other_data) - len(sender_data)) < 200 and
                        abs(other_coverage - coverage) < 0.01):
                    similar_senders += 1  # Found a match

        if similar_senders >= 3:
            reasons.append('coordinated_bot_network')
            details['network_size'] = f"{similar_senders + 1} addresses with identical patterns"

        # Check for regular block spacing
        if len(sender_data) > 100:
            # Sort by block number
            sender_sorted = sender_data.sort_values('block_number')
            # Calculate gaps between consecutive blocks
            block_gaps = sender_sorted['block_number'].diff().dropna()
            # Gap consistency metric
            gap_cv = block_gaps.std() / block_gaps.mean() if block_gaps.mean() > 0 else 0

            if gap_cv < 0.8 and block_gaps.mean() < 10:
                reasons.append('regular_block_spacing')
                details['block_spacing'] = f"Avg gap: {block_gaps.mean():.1f} blocks, CV: {gap_cv:.3f}"

        # Only store if bot criteria were met
        if reasons:
            bot_details[sender] = {
                # List of detection criteria met
                'reasons': reasons,
                'details': details,
                'total_events': len(sender_data),
                'blockchain_coverage': f"{coverage:.3f}"
            }

    return bot_details


def generate_summary_report(df: pd.DataFrame) -> Dict:
    # Get list of orphaned events
    orphans = find_orphan_events(df)
    time_deltas = calculate_time_deltas(df)
    sender_contracts = map_senders_to_contracts(df)
    sender_rankings = rank_senders_by_activity(df)
    quality = analyze_data_quality(df)
    bots = detect_bots(df)

    report = {
        'data_overview': {
            'total_events': len(df),
            'unique_contracts': df['contract_address'].nunique(),
            'unique_senders': df['sender'].nunique(),
            'date_range': f"{df['block_timestamp'].min()} to {df['block_timestamp'].max()}"
        },
        'orphan_events': {
            'count': len(orphans),
            'event_ids': orphans
        },
        'contract_time_deltas': {
            'average_seconds_between_events': time_deltas
        },
        'sender_analysis': {
            'total_unique_senders': len(sender_contracts),
            'top_5_most_active': sender_rankings[:5],
            'sender_contract_mapping_sample': dict(list(sender_contracts.items())[:5]),
            'sender_peak_blocks': find_sender_peak_blocks(df)[:10]
        },
        'data_quality': quality,
        'bot_detection': {
            'suspected_bots': list(bots.keys()) if isinstance(bots, dict) else bots,
            'count': len(bots) if isinstance(bots, dict) else len(bots),
            'details': bots if isinstance(bots, dict) else {}
        }
    }

    return report


def visualize_event_type_frequency(df: pd.DataFrame) -> None:
    """Create bar chart and pie chart for event type distribution"""
    # Create figure with subplots
    plt.figure(figsize=(12, 6))
    # Count occurrences of each event type
    event_counts = df['event_type'].value_counts()

    # First subplot for bar chart
    plt.subplot(1, 2, 1)
    event_counts.plot(kind='bar', color='skyblue', edgecolor='black')
    # Create bar chart
    plt.title('Event Type Frequency Distribution')
    plt.xlabel('Event Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45)
    # Add horizontal grid lines
    plt.grid(axis='y', alpha=0.3)

    # Second subplot for pie chart
    plt.subplot(1, 2, 2)
    # Create pie chart with percentages
    plt.pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%', startangle=90)
    plt.title('Event Type Distribution (Pie Chart)')

    # Adjust subplot spacing
    plt.tight_layout()
    plt.savefig('event_type_frequency.png', dpi=300, bbox_inches='tight')
    plt.show()

    print(f"Event Type Analysis:")
    print(f"Total unique event types: {len(event_counts)}")
    for event_type, count in event_counts.head(10).items():
        print(f"  {event_type}: {count:,} events ({count / len(df) * 100:.1f}%)")
