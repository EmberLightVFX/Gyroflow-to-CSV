import json, zlib, sys, struct, csv, os, math, argparse

parser = argparse.ArgumentParser(
    description='''Convert your Gyroflow stabilization to a CSV file.
    Make sure to choose "including processed gyro data" when exporting from gyroflow.
    As default it saves out the rotations as Euler rotation (ZYX).
    It also saves out the data for your footages FPS'''
)
parser.add_argument("gyroflow_path", help="The path to your Gyroflow file")
parser.add_argument("-s", "--smoothed", help="Calculate from smoothed quaternions",
                    action="store_true")
parser.add_argument("-q", "--quaternions", help="Save data as quaternions",
                    action="store_true")
parser.add_argument("-a", "--all_timestamps", help="Save all timestamps instead of FPS converted",
                    action="store_true")
parser.parse_args()

gyroflow = args.gyroflow_path
convert_to_euler = True
csv_fields = ["timestamp", "x", "y", "z"]
csv_rows = []
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

f = open(gyroflow)
data = json.load(f)
csv_file = os.path.split(gyroflow)
csv_file = os.path.abspath(os.path.join(csv_file[0], os.path.splitext(csv_file[1])[0] + ".csv"))
frame_as_microsec = 1/(data['video_info']['fps']/1000000)

base91_alphabet = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
    'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '!', '#', '$',
    '%', '&', '(', ')', '*', '+', ',', '.', '/', ':', ';', '<', '=',
    '>', '?', '@', '[', ']', '^', '_', '`', '{', '|', '}', '~', '"']

decode_table = dict((v,k) for k,v in enumerate(base91_alphabet))

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
    result = min(abs(ref-first[0]), abs(ref-second[0]))
    if result == first[0]:
        return first
    else:
        return second

# Quaternions
raw = zlib.decompress(decode(data['gyro_source'][quaternion_type]))
length = struct.unpack('<Q', raw[:8])[0]
item_length = len(list(struct.iter_unpack('<qQdddd', raw[8:])))
cur_item = 0
old_percentage = 0
print("Processing gyro data 0%")
if all_timestamps:
    for item in struct.iter_unpack('<qQdddd', raw[8:]):
        timestamp_us, _, x, y, z, w = item
        if convert_to_euler:
            converted = [timestamp_us]
            converted.extend(quaternion_to_euler_angle(x, y, z, w))
            #converted.extend([x, y, z, w])
            csv_rows.append(converted)
        else:
            csv_rows.append([timestamp_us, x, y, z, w])
        if old_percentage <= int(((cur_item+1)/item_length)*100):
            old_percentage = int(((cur_item+1)/item_length)*100)
            print("Processing gyro data", str(int(((cur_item+1)/item_length)*100)) + "%")
        cur_item = cur_item+1
else:
    cur_microsec = 0
    microsec_itterator = 0
    old_data = [0]
    new_data = [0]
    for item in struct.iter_unpack('<qQdddd', raw[8:]):
        timestamp_us, _, x, y, z, w = item
        new_data = [timestamp_us, x, y, z, w]
        if new_data[0] > cur_microsec:
            qdata = closest(timestamp_us, old_data, new_data)

            if convert_to_euler:
                converted = [qdata[0]]
                converted.extend(quaternion_to_euler_angle(qdata[1], qdata[2], qdata[3], qdata[4]))
                csv_rows.append(converted)
            else:
                csv_rows.append(qdata)

            microsec_itterator = microsec_itterator + 1
            cur_microsec = frame_as_microsec * microsec_itterator
        old_data = new_data
        if old_percentage < int(((cur_item+1)/item_length)*100):
            old_percentage = int(((cur_item+1)/item_length)*100)
            print("Processing gyro data", str(int(((cur_item+1)/item_length)*100)) + "%")
        cur_item = cur_item+1

print("Writing to CSV")
with open(csv_file, 'w', newline='') as csvfile: 
    # creating a csv writer object 
    csvwriter = csv.writer(csvfile) 
        
    # writing the fields 
    csvwriter.writerow(csv_fields) 
        
    # writing the data rows 
    csvwriter.writerows(csv_rows)
print("Done")