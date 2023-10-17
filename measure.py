import csv
import numpy as np
from matplotlib import pyplot as plt

if __name__ == "__main__":
    with open("res-core.csv", "r") as f:
        res = csv.reader(f)
        improvement = []
        absolute = []
        is_before = True
        for line in res:
            if line[0] == "benchmark" or line[2] == "timeout":
                is_before = True
                continue
            if is_before:
                before = int(line[2])
                is_before = False
            else:
                after = int(line[2])
                improvement.append((before - after) / before)
                absolute.append(before - after)
                is_before = True
            #print(line)
    print("List of relative improvements for core:")
    print(improvement)
    print("Mean of relative improvements for core:")
    print(np.mean(improvement))
    print("std of relative improvements for core:")
    print(np.std(improvement))
    print("List of absolute improvements for core:")
    print(absolute)
    print("Mean of absolute improvements for core:")
    print(np.mean(absolute))
    print("std of absolute improvements for core:")
    print(np.std(absolute))
    fig, (ax1, ax2) = plt.subplots(1, 2)
    ax1.hist(improvement)
    ax2.hist(absolute)
    plt.show()
    
    with open("res-float.csv", "r") as f:
        res = csv.reader(f)
        improvement = []
        absolute = []
        is_before = True
        for line in res:
            if line[0] == "benchmark" or line[2] == "timeout":
                is_before = True
                continue
            if is_before:
                before = int(line[2])
                is_before = False
            else:
                after = int(line[2])
                improvement.append((before - after) / before)
                absolute.append(before - after)
                is_before = True
            #print(line)
    print("List of relative improvements for float:")
    print(improvement)
    print("Mean of relative improvements for float:")
    print(np.mean(improvement))
    print("std of relative improvements for float:")
    print(np.std(improvement))
    print("List of absolute improvements for float:")
    print(absolute)
    print("Mean of absolute improvements for float:")
    print(np.mean(absolute))
    print("std of absolute improvements for float:")
    print(np.std(absolute))