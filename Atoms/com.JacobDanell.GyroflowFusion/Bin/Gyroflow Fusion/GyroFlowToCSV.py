import json, zlib, sys, struct, csv, os, math, argparse

parser = argparse.ArgumentParser(
    description='''Convert your Gyroflow stabilization to a CSV file.
    Make sure to choose "including processed gyro data" when exporting from gyroflow.
    As default it saves out the rotations as Euler rotation (ZYX).
    It also saves out the data in your footages native frame rate.'''
)
parser.add_argument("gyroflow_path", help="The path to your Gyroflow file")
parser.add_argument("-s", "--smoothed", help="Calculate from smoothed quaternions",
                    action="store_true")
parser.add_argument("-q", "--quaternions", help="Save data as quaternions",
                    action="store_true")
parser.add_argument("-a", "--all_timestamps", help="Save all timestamps instead of FPS converted",
                    action="store_true")
args = parser.parse_args()

# Arg vaiables
gyroflow = args.gyroflow_path
convert_to_euler = True
csv_fields = ["timestamp", "x", "y", "z"]
all_timestamps = False

if args.smoothed:
    quaternion_type = "smoothed_quaternions"
else:
    quaternion_type = "integrated_quaternions"

if args.quaternions:
    convert_to_euler = False
    csv_fields.append("w")

if args.all_timestamps:
    all_timestamps = True

# Global variables
base91_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$',
    '%', '&', '(', ')', '*', '+', ',', '.', '/', ':', ';', '<', '=',
    '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~', '"']

decode_table = dict((v,k) for k,v in enumerate(base91_alphabet))

# Global functions
def decode(encoded_str):
    ### Decode Base91 string to a bytearray ###
    v = -1
    b = 0
    n = 0
    out = bytearray()
    for strletter in encoded_str:
        if not strletter in decode_table:
            continue
        c = decode_table[strletter]
        if(v < 0):
            v = c
        else:
            v += c*91
            b |= v << n
            n += 13 if (v & 8191)>88 else 14
            while True:
                out += struct.pack('B', b&255)
                b >>= 8
                n -= 8
                if not n>7:
                    break
            v = -1
    if v+1:
        out += struct.pack('B', (b | v << n) & 255 )
    return out

def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def quaternion_to_euler_angle(x, y, z, w):
    ysqr = y * y

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + ysqr)
    X = math.degrees(math.atan2(t0, t1))

    t2 = +2.0 * (w * y - z * x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    Y = math.degrees(math.asin(t2))

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (ysqr + z * z)
    Z = math.degrees(math.atan2(t3, t4))

    return [X, Y, Z]

def closest(ref, first, second):
    result = min(abs(ref-first), abs(ref-second))
    if result == abs(ref-first):
        return first
    else:
        return second

# Closest number in a list
def closest2(lst, K):
    if lst.get(K):
        return (K,) + lst.get(K)
    else:
        closest_key = min(lst.keys(), key = lambda key: abs(key-K))
        return (closest_key,) + lst[closest_key]

def offset_at_timestamp(offsets, timestamp_ms):
    if len(offsets) == 0:
        return 0.0
    elif len(offsets) == 1:
        return list(offsets.values())[0]
    else:
        first_ts = int(list(offsets.keys())[0])
        last_ts = int(list(offsets.keys())[-1])

        lookup_ts = min(max(timestamp_ms, first_ts), last_ts)

        offs1 = None
        for key, val in offsets.items():
            if int(key) <= lookup_ts:
                offs1 = int(key)
        if offs1 == lookup_ts:
            return offsets[str(offs1)]
        offs2 = None
        for key, val in offsets.items():
            if int(key) > lookup_ts:
                offs2 = int(key)
                break
        time_delta = offs2 - offs1
        fract = (timestamp_ms - offs1) / time_delta
        return offsets[str(offs1)] + (offsets[str(offs2)] - offsets[str(offs1)]) * fract

def convert_to_dict(data_list):
    data_dict = {}
    for item in data_list:
        data_dict.update({int(item[0]): item[2::]})
    return data_dict

# Quaternions
def process():

    if not os.path.exists(gyroflow):
        print(gyroflow, "was not found")
        return
    f = open(gyroflow)
    data = json.load(f)
    csv_rows = []
    csv_file = os.path.split(gyroflow)
    csv_file = os.path.abspath(os.path.join(csv_file[0], os.path.splitext(csv_file[1])[0] + ".csv"))
    frame_as_microsec = 1/(data['video_info']['fps']/1000000)

    print("Decompress quaternion")
    try:
        raw = zlib.decompress(decode(data['gyro_source'][quaternion_type]))
    except Exception as e:
        print("No quaternions found. Make sure you have saved out your CineFlow file including processed gyro data")
        return
        
    offsets = []
    try:
        offsets = data['offsets']
        for key, val in offsets.items(): # Convert from milliseconds to microseconds
            offsets[key] = val*1000
    except Exception as e:
        pass

    print("Unpacking")
    length = struct.unpack('<Q', raw[:8])[0]
    old_percentage = 0
    gyro_data = list(struct.iter_unpack('<qQdddd', raw[8:]))
    gyro_data = convert_to_dict(gyro_data)

    item_length = len(gyro_data)
    
    printProgressBar(0, item_length, prefix = 'Processing gyro data:', suffix = 'Complete', length = 50)
    if all_timestamps:
        for i, (timestamp, val) in enumerate(gyro_data.items()):

            data = [timestamp]
            if convert_to_euler:
                data.extend(quaternion_to_euler_angle(val[0], val[1], val[2], val[3]))
            else:
                data.extend([val[0], val[1], val[2], val[3]])
            csv_rows.append(data)

            printProgressBar(i + 1, item_length, prefix = 'Processing gyro datas:', suffix = 'Complete', length = 50)
    else:

        num_frames = data['video_info']['num_frames']

        for i in range(num_frames):
            cur_microsec = frame_as_microsec * i
            offset = offset_at_timestamp(offsets, cur_microsec)
            item = closest2(gyro_data, cur_microsec - offset)

            data = [item[0]]
            if convert_to_euler:
                data.extend(quaternion_to_euler_angle(item[1], item[2], item[3], item[4]))
            else:
                data.extend([item[1], item[2], item[3], item[4]])
            csv_rows.append(data)

            printProgressBar(i + 1, num_frames, prefix = 'Processing gyro data:', suffix = 'Complete', length = 50)

    print("Writing to CSV")
    with open(csv_file, 'w', newline='') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 
            
        # writing the fields 
        csvwriter.writerow(csv_fields) 
            
        # writing the data rows 
        csvwriter.writerows(csv_rows)
    print("Done")
process()
