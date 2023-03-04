

def print_num(max):
    line = ''
    # for i in range(0, 6):
    #     for j in range(0, 6):
    #         if i + j <= 5:
    #             line += f'{i} + {j} =\n'

    # for i in range(0, 6):
    #     for j in range(0, 6):
    #         if i >= j:
    #             line += f'{i} - {j} =\n'

    for i in range(0, 6):
        for j in range(0, 6):
            if i != j:
                line += f'{i} ○ {j}\n'
    print(line)


print_num(1)
