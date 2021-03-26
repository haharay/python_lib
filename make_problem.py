'''
原文版本为 highlight.py
简答题：参考文献：https://m.hanspub.org/journal/paper/37823 ALBERT等神经网络模型。
论述题：EASE
'''

import os
import re

import numpy as np
import pandas as pd

#  ￥之间的为需要填写的，#%开头的为提示。不一定H3标题。
#################################################
prob = '''
<h3>
问题题干部分，丫丫
</h3>\n'''
########################
code = """
chipo.item_name.￥value_counts().count()￥
"""
######################################################################
#exec(code.replace('￥', ''))
ZZ = 0  # =0，表示不显示结果，等于array或pandas则显示结果。
frmt = '{:1.0f}'  # 数组显示格式
sol = ''  # 显示答案时的解析步骤

## 这部分设置一般不用修改
expect = re.findall(r'￥(.*?)￥', code)[0]
hints = re.findall(r'#%(.*?)\n', code)
## 清掉答案和帮助文本
code = re.sub(r'￥.*?￥', '_________________________', code)
code = re.sub(r'#%.*?\n', '\n', code)
code = re.sub(r'"', "'", code)  # 以单引号代替双引号


##############################################################
## 把数组和pandas转化为mathjax，用于显示。
def array_disp(ZZ, frmt):
    import array_to_latex as a2l
    from bs4 import BeautifulSoup
    if type(ZZ) == int:
        return ''
    else:
        lx = a2l.to_ltx(ZZ, frmt=frmt, arraytype='bmatrix', print_out=False)
        with open("练习NB/latex_txt.text", 'w') as fa:
            fa.write(lx)
        os.system('pandoc latex_txt.text -s --mathjax --metadata title="latexTxt" -o math_mathjax.html')
        # time.sleep(1.0)
        with open('练习NB/math_mathjax.html', 'r') as fr:
            lines = fr.readlines()
        soup = BeautifulSoup(''.join(lines), 'html.parser')
        return str(soup.find_all('span')[0])


## 处理答案和提示等部分
def ans_hint(expect, sol, hints):
    ss = """
<description>将程序中长下划线部分所缺的代码，填入下框中：</description>  
<customresponse cfn="check_ans" expect="YYYY">
    <textline size="30"/>
</customresponse>
"""
    ss = ss.replace('YYYY', expect)
    if len(sol) > 0:
        ss = ss + """
<solution>
    <div class="detailed-solution">
        <p>XXXXX</p>
    </div>
</solution>        
        """
        ss = ss.replace('XXXXX', sol)
    if len(hints) > 0:
        ss = ss + '<demandhint>' + '\n'
        for ht in hints:
            ss = ss + '      <hint>' + ht + '</hint>\n'
        ss = ss + '</demandhint>'
    ss = ss + '\n</problem>'
    return ss


def main(code, prob, ZZ, frmt, expect, sol, hints):
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonLexer

    ## 两个评分函数，一个比例评分，一个正误评分
    # to do: tfidf的中文评阅
    correct_grader = """
<problem>
<script type="loncapa/python">
def check_ans(expect,answer):
    exp = expect.replace(' ', '')
    ans = answer.replace(' ', '')
    ans = answer.replace('"', "'")
    return exp==ans
import difflib
def check_ratio(expect, answer):
    exp = expect.replace(' ', '')
    ans = answer.replace(' ', '')
    ans = answer.replace('"', "'")
    grade = difflib.SequenceMatcher(None, exp, ans).ratio()
    return {'input_list': [{'ok': True, 'msg': '得分率：'+str(grade), 'grade_decimal': grade}]}
</script>
    """

    code_str = highlight(code, PythonLexer(), HtmlFormatter(noclasses=True))
    ppp = correct_grader + prob + array_disp(ZZ, frmt) + code_str + ans_hint(expect, sol, hints)
    # print(ppp)
    try:
        import clipboard as _clipboard

        _clipboard.copy(ppp)
    except ImportError:
        print('\nPackage ''clipboard'' 没有安装')
        print('pip install clipboard\nor install via other ',
              'means to use this function')


if __name__ == "__main__":
    main(code, prob, ZZ, frmt, expect, sol, hints)
