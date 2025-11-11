import json

stats_file = 'runs/track/750-1/initial_result/all_stats.json'

with open(stats_file, 'r', encoding='utf-8') as f:
    stats = json.load(f)

print('检查 not_use_revolution 的使用情况:')
print('=' * 80)

for key, value in stats.items():
    not_use_rotation = value.get('not_use_rotation', False)
    not_use_revolution = value.get('not_use_revolution', False)
    not_use = value.get('not_use', False)
    margin = value.get('margin', None)
    
    print(f'\nID {key}:')
    print(f'  margin: {margin}')
    print(f'  not_use: {not_use}')
    print(f'  not_use_rotation: {not_use_rotation}')
    print(f'  not_use_revolution: {not_use_revolution}')

print('\n' + '=' * 80)
print('总结：')
print(f'总记录数: {len(stats)}')
rev_true = sum(1 for v in stats.values() if v.get('not_use_revolution', False))
rev_false = len(stats) - rev_true
print(f'not_use_revolution=True: {rev_true}')
print(f'not_use_revolution=False: {rev_false}')
