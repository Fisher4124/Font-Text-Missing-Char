import os
import struct
import platform
import datetime

def get_text_characters(txt_path):
    """读取TXT文件所有字符"""
    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()
    return set(text)

def get_ttf_characters(ttf_path):
    """从TTF文件中解析cmap表，提取字体支持的字符"""
    chars = set()
    with open(ttf_path, "rb") as f:
        data = f.read()

    # 读取表目录
    numTables = struct.unpack(">H", data[4:6])[0]
    offset = 12
    cmap_offset = None

    # 找到cmap表的偏移量
    for _ in range(numTables):
        tag = data[offset:offset + 4].decode(errors="ignore")
        _, tableOffset, _ = struct.unpack(">III", data[offset + 4:offset + 16])
        if tag == "cmap":
            cmap_offset = tableOffset
            break
        offset += 16

    if cmap_offset is None:
        print("未找到cmap表，无法分析字体字符集。")
        return chars

    # 解析cmap表头
    _, numSubtables = struct.unpack(">HH", data[cmap_offset:cmap_offset + 4])
    sub_offset = cmap_offset + 4

    # 遍历子表，寻找Unicode子表（平台ID=3, 编码ID=1或10）
    for _ in range(numSubtables):
        platformID, encodingID, subtable_offset = struct.unpack(">HHI", data[sub_offset:sub_offset + 8])
        if platformID == 3 and encodingID in (1, 10):  # Windows Unicode
            cmap_table_offset = cmap_offset + subtable_offset
            format_type = struct.unpack(">H", data[cmap_table_offset:cmap_table_offset + 2])[0]

            # format 4
            if format_type == 4:
                segCount = struct.unpack(">H", data[cmap_table_offset + 6:cmap_table_offset + 8])[0] // 2
                endCode_offset = cmap_table_offset + 14
                endCodes = struct.unpack(f">{segCount}H", data[endCode_offset:endCode_offset + segCount * 2])
                startCode_offset = endCode_offset + 2 + segCount * 2
                startCodes = struct.unpack(f">{segCount}H", data[startCode_offset:startCode_offset + segCount * 2])
                for i in range(segCount):
                    for code in range(startCodes[i], endCodes[i] + 1):
                        chars.add(chr(code))
            # format 12
            elif format_type == 12:
                nGroups = struct.unpack(">I", data[cmap_table_offset + 12:cmap_table_offset + 16])[0]
                group_offset = cmap_table_offset + 16
                for _ in range(nGroups):
                    startCharCode, endCharCode, _ = struct.unpack(">III", data[group_offset:group_offset + 12])
                    for code in range(startCharCode, endCharCode + 1):
                        chars.add(chr(code))
                    group_offset += 12
        sub_offset += 8

    return chars


def get_desktop_path():
    """自动检测桌面路径"""
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.path.join(os.environ["USERPROFILE"]), "Desktop")
    else:
        return os.path.join(os.path.expanduser("~"), "Desktop")


def find_missing_characters(txt_path, ttf_path):
    text_chars = get_text_characters(txt_path)
    font_chars = get_ttf_characters(ttf_path)
    missing_chars = sorted(text_chars - font_chars)

    print(f"\n字体中缺失的字符数量：{len(missing_chars)}")
    print("缺失的字符如下：")
    print("".join(missing_chars))

    # 保存到桌面并加上时间戳
    desktop = get_desktop_path()
    date_tag = datetime.datetime.now().strftime("%y%m%d_%H%M%S")  # 生成 YYMMDD_HHMMSS 格式
    output_filename = f"missing_chars_{date_tag}.txt"
    output_path = os.path.join(desktop, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("".join(missing_chars))

    print(f"\n完毕！结果已保存至：{output_path}")

while True:
    txt_path = input("请输入TXT文本路径：").strip()
    ttf_path = input("请输入TTF/OTF字体路径：").strip()
    find_missing_characters(txt_path, ttf_path)
    
    choice = input("\n按回车键重新运行／[ENTER]=ReRun")
    if choice.strip() == "":
        print("\n=== 重新运行 ===\n")
        continue
    else:
        break
