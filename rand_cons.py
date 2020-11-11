import numpy as np

def rem_chosen(val_left, current_chosen):
    """
        Function to remove one occurrence of an integer in a numpy array
    """
    where_chosen = np.argwhere(val_left == current_chosen).flatten()
    remove_one_chosen = np.random.choice(where_chosen)
    val_left = np.delete(val_left, remove_one_chosen)
    return val_left

def check_twoD(ordered_array, current_chosen, i, coords):
    """
        Function to check whether a chosen position is valid in a 2-D grid (n x n)
    """
    previous_chosen = ordered_array[-int(i)]
    previous_coords = coords[str(int(previous_chosen))]
    current_coords = coords[str(int(current_chosen))]
    
    row_diff = abs(current_coords[0] - previous_coords[0])
    column_diff = abs(current_coords[1] - previous_coords[1])
    
    if row_diff != column_diff and any(c == 1 for c in [row_diff, column_diff]) and any(c == 0 for c in [row_diff, column_diff]):
        print(f'\nInvalid choice at position {-int(i)}\n')
        return False
    elif previous_chosen == current_chosen[0]:
        print(f'\nInvalid choice at position {-int(i)}\n')
        return False
    else:
        print(f'\nValid choice at position {-int(i)}\n')
        return True


def check_linear(ordered_array, current_chosen, i, coords = None):
    """
        Function to check whether a chosen position is valid in a line
    """
    previous_chosen = ordered_array[-int(i)]
    
    if previous_chosen == current_chosen[0]:
        print(f'\nInvalid choice at position {-int(i)}\n')
        return False
    else:
        print(f'\nValid choice at position {-int(i)}\n')
        return True

def randomise_constraints(val_left, ordered_array, count, func, limit = 2, coords= None):
    """
       Recursive function to randomise with constraints
    """
    count += 1
    if len(val_left) == 0:
        printme('Constraint randomisation done..')
    
    elif count > 100:
        return False

    elif len(ordered_array) == 0:
        printme('First value in...')
        current_chosen = np.random.choice(val_left, 1, replace=False)
        ordered_array.append(int(current_chosen))
        val_left = rem_chosen(val_left, current_chosen)
        randomise_constraints(val_left, ordered_array, count, func, limit, coords)
    
    else:
        current_chosen = np.random.choice(val_left, 1, replace=False)
        backwards = []
        for i in np.arange(1, limit + 0.1, 1):
            if len(ordered_array) < i:
                break
            
            current_check = func(ordered_array, current_chosen, i, coords)
            backwards.append(current_check)

        if np.all(backwards):
            print('Another value in...')
            ordered_array.append(int(current_chosen))
            val_left = rem_chosen(val_left, current_chosen)
            randomise_constraints(val_left, ordered_array, count, func, limit, coords)
        else:
            randomise_constraints(val_left, ordered_array, count, func, limit, coords)

    return ordered_array

def exp_rand(init_rep, check_twoD, coor_cells=None):
    """
        Function to converge randomisation with constraints algorithm 
    """
    while True:
        final_order = []
        final_order = randomise_constraints(init_rep, final_order, 0, check_twoD, coords= coor_cells)
        if len(final_order) < len(init_rep):
            printme("Didn't converge...")
        else:
            printme('Constraint randomisation done')
            break
    return final_order