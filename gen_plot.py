import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Initialize dictionaries to store data
latency_data = {}
deadline_data = {}

# Read latency.txt and store data
with open('latency.txt', 'r') as f:
    for line in f:
        parts = line.strip().split(", ")
        timestamp = float(parts[0].split(" - latency: ")[0])
        inside_time = float(parts[0].split(":")[3])
        deadline = int(parts[2].split(": ")[1])
        latency_percentage = (inside_time / deadline) * 100
        if timestamp in latency_data:
            timestamp += 1  # Ensure unique timestamps
        latency_data[timestamp] = latency_percentage
        deadline_data[timestamp] = deadline

# Convert latency_data and deadline_data to Pandas DataFrames for easier manipulation
latency_df = pd.DataFrame(list(latency_data.items()), columns=['Timestamp', 'Latency'])
deadline_df = pd.DataFrame(list(deadline_data.items()), columns=['Timestamp', 'Deadline'])

# Merge latency_df and deadline_df
latency_df = latency_df.merge(deadline_df, on='Timestamp')

# Define colors for each distinct deadline value
colors = {
    5: 'red',
    30: 'blue',
    100: 'green',
    1500: 'purple'
}

# Map the colors to the deadlines
latency_df['Color'] = latency_df['Deadline'].map(colors)

# Plotting
plt.figure(figsize=(10, 5))

# Latency plot with colored dots based on deadline values
sc = plt.scatter(latency_df['Timestamp'], latency_df['Latency'],
                 c=latency_df['Color'], marker='o', s=20)
plt.axhline(y=100, color='gray', linestyle='--', label='Threshold: 100')
plt.ylabel('Latency (%)')
plt.title('Latency Over Time')
plt.legend()

# Create a legend manually
handles = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=f'Deadline: {deadline}')
           for deadline, color in colors.items()]
plt.legend(handles=handles, title='Deadline Values')

# Formatting the x-axis with timestamps
plt.xlabel('Timestamp')
plt.tight_layout()
plt.savefig('latency_plot.png')
plt.show()
