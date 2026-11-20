L = int(input())
H = int(input())
cows = H // 2          # у каждой коровы 2 рога
horses = L // 4 - cows  # всего животных L/4, остальные — лошади
print(cows, horses)
