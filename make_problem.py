import os
import re
import pandas as pd
import numpy as np
from markdown import markdown
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from subprocess import check_output
#  ￥之间的为需要填写的，#%开头的为提示。
#################################################
prob = '''
题目要求：
编写一个Python程序，从example.com中抓取h1标签。

'''
###————————————————————————————————————————————————————
code_source = """
from urllib.request import urlopen
from bs4 import BeautifulSoup
html = urlopen('http://www.example.com/')
bsh = ￥BeautifulSoup￥(html.read(), 'html.parser')
print(bsh.h1)
"""
###########################################################
###########################################################
"""
其它备注信息：
1. with ... as ...语句用于方便的处理文件打开、读写、关闭过程中的异常。

原文版本为 highlight.py
简答题：参考文献：https://m.hanspub.org/journal/paper/37823 ALBERT等神经网络模型。
论述题：EASE
"""
######################################################################
#exec(code.replace('￥', ''))
ZZ = 1  # =0，表示不执行程序；==1:执行程序，并显示结果；==2, 返回名为df或result的array或pandas对象时则显示结果。
frmt = '{:1.0f}'  # 数组显示格式
sol = ''  # 显示答案时的解析步骤



## 这部分设置一般不用修改
expect = re.findall(r'￥(.*?)￥', code_source)[0]
hints = re.findall(r'#%(.*?)\n', code_source)
## 清掉答案和帮助文本
code = re.sub(r'￥.*?￥', '_________________________', code_source)
code = re.sub(r'#%.*?\n', '\n', code)
code = re.sub(r'"', "'", code)  # 以单引号代替双引号
code_exec = re.sub(r'￥', '', code_source)

##############################################################
## 把数组和pandas转化为mathjax，用于显示。
def array_disp(ZZ, frmt):
    import array_to_latex as a2l
    from bs4 import BeautifulSoup
    global code_exec
    if ZZ==0:
        return ''
    elif ZZ==1:
        with open("./test001.py", 'w') as fa:
            fa.write(code_exec)
        lines = check_output("python3 ./test001.py", shell=True).decode('utf-8')
        lines = lines.replace('<', '&lt;')
        lines = lines.replace('>', '&gt;')
        lines = '执行上述程序，输出:\n'+lines
        print(lines)
        return markdown(lines.replace('\n', '<br/>'))
    elif ZZ==2:
        exec(code_exec)
        if 'df' in locals():
            df =df
        elif 'result' in locals():
            df = result
        else:
            print('找不到ndarray或pandas的结果变量')
        lx = a2l.to_ltx(df, frmt=frmt,
                            arraytype='bmatrix', print_out=False)
        with open("./latex_txt.text", 'w') as fa:
            fa.write(lx)
        os.system('pandoc latex_txt.text -s --mathjax --metadata title="latexTxt" -o math_mathjax.html')
        # time.sleep(1.0)
        with open('./math_mathjax.html', 'r') as fr:
            lines = fr.readlines()
        soup = BeautifulSoup(''.join(lines), 'html.parser')
        return str(soup.find_all('span')[0])
    else:
        return ''


## 处理答案和提示等部分
def ans_hint(expect, sol, hints):
    ss = """
    <description>将程序中长下划线部分所缺的代码，填入下框中（请使用单引号）：</description>  
    <customresponse cfn="check_ans" expect="YYYY">
        <textline size="30"/>
    </customresponse>
    """
    ss = ss.replace('YYYY', expect)
    detail_solution = """
    <solution>
    <div class="detailed-solution">
        <p>解析：</p>
    <iframe src="https://trinket.io/embed/python3/9d578a67e3" width="100%" height="356" frameborder="0" marginwidth="0" marginheight="0" allowfullscreen="false"></iframe>
    </div>
    </solution>
    """
    ss = ss + detail_solution
    if len(sol) > 0:
        ss = ss.replace('解析：', sol)
    if len(hints) > 0:
        ss = ss + '<demandhint>' + '\n'
        for ht in hints:
            ss = ss + '      <hint>' + ht + '</hint>\n'
        ss = ss + '</demandhint>'
    ss = ss + '\n</problem>'
    return ss


def main(code, prob, ZZ, frmt, expect, sol, hints):
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
    prob = markdown(prob.replace('\n', '<br/>'))
    ppp = correct_grader + prob + code_str +\
        array_disp(ZZ, frmt) + ans_hint(expect, sol, hints)
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
