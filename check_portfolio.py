#!/usr/bin/env python3

total_sol = 0.342809
sol_price = 150.13
total_usd = total_sol * sol_price

print('💰 FAKTYCZNY STAN PORTFOLIO:')
print(f'📊 Total SOL: {total_sol:.6f} SOL')
print(f'💵 Total USD: ${total_usd:.2f}')
print(f'🎯 Target: 2.0 SOL (${2.0 * sol_price:.2f})')
print(f'📈 Progress: {(total_sol/2.0)*100:.1f}%')
print(f'💎 Needed: {2.0 - total_sol:.6f} SOL (${(2.0 - total_sol) * sol_price:.2f})')
print(f'🚀 Multiplier needed: {2.0/total_sol:.1f}x')
