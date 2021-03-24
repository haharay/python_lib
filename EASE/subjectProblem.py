"""
参考文献：https://m.hanspub.org/journal/paper/37823 ALBERT等神经网络模型。
"""


from sklearn.feature_extraction.text import TfidfVectorizer

import jieba
from gensim import corpora, models, similarities

# 目标：计算相似度，根据相似度来评分主观题。

text = """我是一条天狗呀！
我把月来吞了，
我把日来吞了，
我把一切的星球来吞了，
我把全宇宙来吞了。
我便是我了！"""
sentences = text.split()
sent_words = [list(jieba.cut(si)) for si in sentences]
document = [" ".join(sw) for sw in sent_words]

doc0 = "我不喜欢上海"
doc1 = "上海是一个好地方"
doc2 = "北京是一个好地方"
doc3 = "上海好吃的在哪里"
doc4 = "上海好玩的在哪里"
doc5 = "上海是好地方"
doc6 = "上海路和上海人"
doc7 = "喜欢吃上海小吃"
doc_test ="我喜欢上海的小吃"

all_doc = []
all_doc.append(doc0)
all_doc.append(doc1)
all_doc.append(doc2)
all_doc.append(doc3)
all_doc.append(doc4)
all_doc.append(doc5)
all_doc.append(doc6)
all_doc.append(doc7)


# 制作语料库
all_doc_list = [list(jieba.cut(si)) for si in all_doc]
dic = corpora.Dictionary(all_doc_list)   #获取词袋
corpus = [dic.doc2bow(doc) for doc in all_doc_list]  #制作语料库

doc_test_list = [word for word in jieba.cut(doc_test)]
doc_test_vec = dic.doc2bow(doc_test_list)



# 相似度分析
tfidf = models.TfidfModel(corpus)  #TF-IDF对语料库建模
index = similarities.SparseMatrixSimilarity(tfidf[corpus], num_features=len(dic.keys()))
sim = index[tfidf[doc_test_vec]]
sorted(enumerate(sim), key=lambda item: -item[1])

print(document)


#7.创建索引
index = similarities.MatrixSimilarity(tfidf[corpus])
# 8.相似度计算
new_vec_tfidf = tfidf[doc_test_vec]  # 将要比较文档转换为tfidf表示方法
print(new_vec_tfidf)

# 计算要比较的文档与语料库中每篇文档的相似度
sims = index[new_vec_tfidf]
print(sims)


