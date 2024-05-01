import re
from pypinyin import Style, lazy_pinyin


def contains_chinese(s):
    return any('\u4e00' <= c <= '\u9fff' for c in s)


def first_letter(s):
    """将字符串s中的中文部分转为拼音首字母，非中文部分保持不变."""
    result = []
    for char in s:
        if '\u4e00' <= char <= '\u9fff':  # 如果是中文字符
            result.append(lazy_pinyin(char, style=Style.FIRST_LETTER)[0])
        else:
            result.append(char)
    return ''.join(result)


def search(key, data_list):
    result = set()

    # 如果关键词包含中文，直接返回匹配列表
    if contains_chinese(key):
        for item in data_list:
            if key in item:
                result.add(item)
        return result

    # 如果关键词不含任何中文，看是否完全由英文字母组成（假定这代表有可能是拼音）
    if re.search('[A-Za-z]', key):
        # 匹配流程，将候选集中包含中文的元素处理成首字母的拼音进行匹配
        for item in data_list:
            if contains_chinese(item):  # 如果元素包含中文
                converted_item = first_letter(item)  # 转换为首字母拼音
                # 进行匹配
                if key in converted_item:
                    result.add(item)
            else:
                # 如果候选元素不含中文，直接匹配
                if key in item:
                    result.add(item)
    else:
        for item in data_list:
            if key in item:
                result.add(item)
        return result
    return result


# 样本数据
# str_list = ['杭州', 'hz11', '33hz', 'hxz', 'hz', '浙江杭州', '杭州11', '11-11']
#
# # 搜索关键词示例
# keywords = ['杭州', 'hz', 'hz11', '11', '-', '杭', 'hangzhou']
#
# # 进行搜索并打印结果
# for keyword in keywords:
#     matching_items = search(keyword, str_list)
#     print(f"搜索 '{keyword}' 得到的结果: {matching_items}")

