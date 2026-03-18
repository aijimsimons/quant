"""Debug position calculation."""

import sys
sys.path.insert(0, '/Users/xingjianliu/jim/quant')

capital = 10000.0
position_size_pct = 0.05
entry_price = 82704.79

position_value = capital * position_size_pct
print(f'Position value: {position_value}')
print(f'Position: {int(position_value / entry_price)}')

# Check the calculation
position = int(position_value / entry_price)
print(f'Position * price: {position * entry_price}')
print(f'Capital: {capital}')
print(f'Exceeds capital? {position * entry_price > capital}')

# Calculate max position
max_position = int(capital / entry_price)
print(f'Max position: {max_position}')

# The issue: position is 0 because 10000 / 82704 < 1
# For Bitcoin at $82k, with $10k capital, you can only buy 0.12 units
# But int(0.12) = 0

print('\n=== Solution ===')
# For crypto, use fractional positions or min position size
min_position_value = 100  # Minimum $100 per trade
if position_value < min_position_value:
    position_value = min_position_value
position = int(position_value / entry_price)
print(f'With min position: {position}')
