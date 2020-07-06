
def calculate(strs):
    if '\u4e00' <= strs <= '\u9fa5':
        return strs
    try:
        if "?" in strs or "=" in strs:
            strs = strs.replace("?", "")
            strs = strs.replace("JIA", "")
            strs = strs.replace("JA", "")
            strs = strs.replace("加", "")
            strs = strs.replace("+", "")
            strs = strs.replace("=", "-")

        else:
            strs = strs.replace(" ", "")
            strs = strs.replace("ADD", "+")
            strs = strs.replace("JIA", "+")
            strs = strs.replace("JA", "+")
            strs = strs.replace("加", "+")
            strs = strs.replace("CHENG", "*")
            strs = strs.replace("CHEN", "*")
            strs = strs.replace("乘", "*")
            strs = strs.replace("剩", "*")

        code = abs(eval(strs))
    except Exception as e:
        code = strs
        print(e)
    print("计算得：", code)
    return code
