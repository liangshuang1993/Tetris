import numpy as np

def add_block_to_bg(block, centor, pos, bg):
    '''
    block: block array
    centor: centor of array(row, column)
    pos: block's centor position in bg(x, y)
    bg: bg array
    '''
    x, y = pos
    # block's position in background
    first_row = y + centor[0]
    last_row = y + centor[0] + block.shape[0] - 1
    first_col = x - centor[1]
    last_col = x - centor[1] + block.shape[1] - 1

    value = np.copy(bg)
    # add to background
    for i, row in enumerate(range(first_row, last_row + 1)):
        for j, col in enumerate(range(first_col, last_col + 1)):
            value[row, col] += block[i, j] 
    
    return value
