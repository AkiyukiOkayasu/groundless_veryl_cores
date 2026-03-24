import math

# --- 設定 ---
ADDR_BITS = 10
DATA_BITS = 31 # 1/4周期の正弦波を生成するため、符号ビットを考慮して31ビットに設定
ENTRIES = 2 ** ADDR_BITS     # 1024
MAX_VAL = (2 ** DATA_BITS) - 1
FILENAME = "sine_data.txt"

print(f"Generating {FILENAME} ...")

with open(FILENAME, "w") as f:
    for i in range(ENTRIES):
        angle = (i / ENTRIES) * (math.pi / 2)
        val = int(math.sin(angle) * MAX_VAL)

        hex_str = f"{val:08x}"
        suffix = "," if i < ENTRIES - 1 else ""
        f.write(f"31'h{hex_str}{suffix}\n")

print("Done.")
